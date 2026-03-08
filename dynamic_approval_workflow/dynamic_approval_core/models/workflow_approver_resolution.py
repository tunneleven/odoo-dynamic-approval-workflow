import json
from json import JSONDecodeError

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

from ..exceptions import WorkflowConfigurationError, WorkflowRuntimeError, WorkflowSecurityPolicyError


class WorkflowApproverResolution(models.Model):
    """Approver source rules per workflow node and version."""

    _name = "workflow.approver.resolution"
    _description = "Workflow Approver Resolution Rule"
    _order = "sequence, id"

    name = fields.Char(size=128, required=True)
    definition_version_id = fields.Many2one(
        "workflow.definition.version",
        required=True,
        ondelete="cascade",
        index=True,
    )
    node_id = fields.Char(
        string="Node ID",
        size=64,
        required=True,
        index=True,
    )
    sequence = fields.Integer(default=10)
    resolution_type = fields.Selection(
        [
            ("user", "Named Users"),
            ("group", "Group"),
            ("role", "Role"),
            ("hierarchy", "Hierarchy"),
            ("field", "Field Path"),
            ("delegate", "Delegate"),
        ],
        required=True,
    )
    user_ids = fields.Many2many("res.users", string="Named Users")
    group_id = fields.Many2one(
        "res.groups",
        ondelete="restrict",
    )
    field_path = fields.Char(size=255)
    hierarchy_levels = fields.Integer(default=1)
    quorum_mode = fields.Selection(
        [
            ("all", "All"),
            ("any", "Any"),
            ("quorum", "Quorum"),
        ],
        default="all",
    )
    quorum_count = fields.Integer()
    quorum_percentage = fields.Float()
    anti_self_approval = fields.Boolean(default=True)
    separation_of_duty_rule = fields.Text()
    fallback_type = fields.Selection(
        [
            ("fallback_group", "Fallback Group"),
            ("fallback_hierarchy_level", "Fallback Hierarchy Level"),
            ("fallback_named_users", "Fallback Named Users"),
            ("fallback_escalation_target", "Fallback Escalation Target"),
        ]
    )
    fallback_group_id = fields.Many2one(
        "res.groups",
        ondelete="set null",
    )
    fallback_user_ids = fields.Many2many(
        "res.users",
        "workflow_resolution_fallback_user_rel",
        string="Fallback Users",
    )
    company_id = fields.Many2one(
        related="definition_version_id.company_id",
        store=True,
        index=True,
        readonly=True,
    )

    @api.constrains(
        "resolution_type",
        "fallback_type",
        "user_ids",
        "group_id",
        "field_path",
        "hierarchy_levels",
    )
    def _check_resolution_source_values(self):
        """Validate source fields required by the selected resolution type."""
        for record in self:
            if record.resolution_type == "user" and not record.user_ids:
                raise ValidationError(_("Named Users are required when type is 'user'."))
            if record.resolution_type in {"group", "role"} and not record.group_id:
                raise ValidationError(_("Group is required when type is 'group' or 'role'."))
            if record.resolution_type == "field":
                if not record.field_path:
                    raise ValidationError(_("Field Path is required when type is 'field'."))
                record._validate_field_path()
            if (
                record.resolution_type == "hierarchy" or record.fallback_type == "fallback_hierarchy_level"
            ) and not 1 <= (record.hierarchy_levels or 0) <= 5:
                raise ValidationError(_("Hierarchy Levels must be between 1 and 5."))

    @api.constrains("quorum_mode", "quorum_count", "quorum_percentage")
    def _check_quorum_configuration(self):
        """Validate quorum-specific values."""
        for record in self:
            if record.quorum_mode != "quorum":
                continue
            if record.quorum_count <= 0:
                raise ValidationError(_("Quorum Count must be greater than zero when Join Mode is 'quorum'."))
            if not 0 < record.quorum_percentage <= 100:
                raise ValidationError(_("Quorum %% must be between 0 and 100 when Join Mode is 'quorum'."))

    @api.constrains("fallback_type", "fallback_group_id", "fallback_user_ids")
    def _check_fallback_configuration(self):
        """Validate fallback source configuration."""
        for record in self:
            if record.fallback_type == "fallback_group" and not record.fallback_group_id:
                raise ValidationError(_("Fallback Group is required when fallback source is 'fallback_group'."))
            if record.fallback_type == "fallback_named_users" and not record.fallback_user_ids:
                raise ValidationError(
                    _("Fallback Users are required when fallback source is 'fallback_named_users'.")
                )
            if record.fallback_type != "fallback_group" and record.fallback_group_id:
                raise ValidationError(_("Fallback Group can only be set for 'fallback_group'."))
            if record.fallback_type != "fallback_named_users" and record.fallback_user_ids:
                raise ValidationError(_("Fallback Users can only be set for 'fallback_named_users'."))

    @api.constrains("field_path")
    def _check_field_path_depth(self):
        """Limit field paths to at most three relational hops."""
        for record in self.filtered("field_path"):
            if len(record._field_path_segments()) > 3:
                raise ValidationError(_("Field Path cannot exceed 3 relational hops."))

    @api.constrains("separation_of_duty_rule")
    def _check_separation_of_duty_rule_json(self):
        """Ensure the SoD rule is valid JSON when configured."""
        for record in self.filtered("separation_of_duty_rule"):
            record._parse_separation_of_duty_rule()

    def resolve_approvers(self, instance_id, context=None):
        """Resolve approvers for one or more ordered rules."""
        instance = self._resolve_instance(instance_id)
        context = dict(context or {})
        ordered_rules = self.sorted(lambda rule: (rule.sequence, rule.id))
        if not ordered_rules:
            self._create_missing_rule_incident(instance, context=context)
            return self.env["res.users"]

        resolved_ids = []
        seen_ids = set()

        for rule in ordered_rules:
            rule_context = dict(context, resolved_approver_ids=list(resolved_ids))
            users = rule._resolve_rule_approvers(instance, context=rule_context, create_incident=False)
            for user in users:
                if user.id in seen_ids:
                    continue
                seen_ids.add(user.id)
                resolved_ids.append(user.id)

        resolved_users = self.env["res.users"].browse(resolved_ids)
        if not resolved_users:
            ordered_rules[0]._create_no_approver_incident(instance, context=context)
        return resolved_users

    def _resolve_approvers(self, instance_id, context=None):
        """Backward-compatible alias for approver resolution."""
        return self.resolve_approvers(instance_id, context=context)

    def _apply_anti_self(self, approver_set, requester_id):
        """Remove the requester when anti-self approval is enabled."""
        self.ensure_one()
        if not self.anti_self_approval or not requester_id:
            return approver_set
        return approver_set.filtered(lambda user: user.id != requester_id)

    def _apply_sod(self, approver_set, prior_decisions):
        """Filter approvers using the configured SoD JSON rule."""
        self.ensure_one()
        rule = self._parse_separation_of_duty_rule()
        if not rule:
            return approver_set

        prior_actor_ids = self._extract_prior_actor_ids(prior_decisions)
        blocked_user_ids = set(rule.get("blocked_user_ids", [])) | set(rule.get("exclude_user_ids", []))
        if rule.get("exclude_prior_actors"):
            blocked_user_ids |= prior_actor_ids

        blocked_group_ids = set(rule.get("blocked_group_ids", [])) | set(rule.get("exclude_group_ids", []))
        blocked_users = self.env["res.users"]
        if blocked_group_ids:
            blocked_groups = self.env["res.groups"].browse(list(blocked_group_ids)).exists()
            blocked_users = self._users_from_group_recordset(blocked_groups)

        blocked_ids = blocked_user_ids | set(blocked_users.ids)
        return approver_set.filtered(lambda user: user.id not in blocked_ids)

    def _evaluate_fallback(self, instance, context=None):
        """Resolve the configured fallback user set."""
        self.ensure_one()
        empty_users = self.env["res.users"]
        fallback_type = self.fallback_type
        if not fallback_type:
            return empty_users

        if fallback_type == "fallback_group":
            return self._normalize_user_recordset(self._users_from_single_group(self.fallback_group_id))

        if fallback_type == "fallback_named_users":
            return self._normalize_user_recordset(self.fallback_user_ids)

        if fallback_type == "fallback_hierarchy_level":
            return self._normalize_user_recordset(
                self._resolve_users_from_hierarchy(instance.requester_id, levels=(self.hierarchy_levels or 1) + 1)
            )

        if fallback_type == "fallback_escalation_target":
            return self._normalize_user_recordset(self._users_from_context(context or {}, "escalation_target"))

        return empty_users

    def _resolve_rule_approvers(self, instance, context=None, create_incident=True):
        """Resolve approvers for a single rule."""
        self.ensure_one()
        resolved_users = self._resolve_source_users(instance, context=context)
        resolved_users = self._filter_resolved_users(
            resolved_users,
            preserve_order=self.resolution_type in {"group", "role", "delegate"},
        )
        policy_filtered_users = self._apply_policy_filters(instance, resolved_users, context=context)
        if policy_filtered_users:
            return policy_filtered_users
        if resolved_users:
            self._raise_policy_block(instance)

        fallback_users = self._evaluate_fallback(instance, context=context)
        fallback_users = self._filter_resolved_users(
            fallback_users,
            preserve_order=self.fallback_type == "fallback_group",
        )
        policy_filtered_fallback = self._apply_policy_filters(instance, fallback_users, context=context)
        if policy_filtered_fallback:
            return policy_filtered_fallback
        if fallback_users:
            self._raise_policy_block(instance)

        if create_incident:
            self._create_no_approver_incident(instance, context=context)
        return self.env["res.users"]

    def _resolve_source_users(self, instance, context=None):
        """Expand the primary approver source configured on the rule."""
        self.ensure_one()
        resolution_type = self.resolution_type
        context = dict(context or {})

        if resolution_type == "user":
            return self._normalize_user_recordset(self.user_ids.sorted("id"), preserve_order=True)

        if resolution_type in {"group", "role"}:
            return self._normalize_user_recordset(
                self._users_from_single_group(self.group_id),
                preserve_order=True,
            )

        if resolution_type == "hierarchy":
            return self._normalize_user_recordset(
                self._resolve_users_from_hierarchy(instance.requester_id, levels=self.hierarchy_levels)
            )

        if resolution_type == "field":
            return self._normalize_user_recordset(self._resolve_users_from_field_path(instance))

        if resolution_type == "delegate":
            return self._normalize_user_recordset(
                self._resolve_users_from_delegate_rules(instance, context),
                preserve_order=True,
            )

        return self.env["res.users"]

    def _filter_resolved_users(self, users, preserve_order=False):
        """Apply active-user filtering to a user set."""
        self.ensure_one()
        return self._normalize_user_recordset(users, preserve_order=preserve_order)

    def _apply_policy_filters(self, instance, users, context=None):
        """Apply anti-self and SoD filters to an already-active user set."""
        self.ensure_one()
        filtered_users = self._apply_anti_self(users, instance.requester_id.id)
        filtered_users = self._apply_sod(filtered_users, (context or {}).get("prior_decisions"))
        return self._normalize_user_recordset(filtered_users, preserve_order=True)

    def _resolve_users_from_field_path(self, instance):
        """Resolve approvers from the instance target record field path."""
        self.ensure_one()
        target_record = self._get_instance_target_record(instance)
        current = target_record
        segments = self._field_path_segments()

        for index, field_name in enumerate(segments):
            if not isinstance(current, models.BaseModel):
                raise WorkflowConfigurationError(
                    _("Field Path '%(path)s' must traverse relational fields only.") % {"path": self.field_path}
                )
            if field_name not in current._fields:
                raise WorkflowConfigurationError(
                    _("Field Path '%(path)s' contains invalid segment '%(segment)s'.")
                    % {"path": self.field_path, "segment": field_name}
                )
            current = current.mapped(field_name)
            if not current:
                return self.env["res.users"]
            if isinstance(current, models.BaseModel):
                continue

            if index < len(segments) - 1:
                raise WorkflowConfigurationError(
                    _("Field Path '%(path)s' segment '%(segment)s' must be relational.")
                    % {"path": self.field_path, "segment": field_name}
                )
            raise WorkflowConfigurationError(
                _("Field Path '%(path)s' must end on a user-compatible relational field.")
                % {"path": self.field_path}
            )

        if current._name not in {"res.users", "res.partner"}:
            raise WorkflowConfigurationError(
                _("Field Path '%(path)s' must end on a user-compatible relational field.")
                % {"path": self.field_path}
            )
        return self._coerce_records_to_users(current)

    def _resolve_users_from_hierarchy(self, requester, levels=None):
        """Resolve manager-chain users when HR data is available."""
        self.ensure_one()
        requester = requester.exists()
        levels = levels or self.hierarchy_levels or 1
        empty_users = self.env["res.users"]
        if not requester:
            return empty_users

        manager = self._get_manager_user(requester)
        resolved_users = empty_users
        current_level = 0
        while manager and current_level < levels:
            resolved_users |= manager
            manager = self._get_manager_user(manager)
            current_level += 1
        return resolved_users

    def _resolve_users_from_delegate_rules(self, instance, context):
        """Resolve active delegates for the requested delegator context."""
        self.ensure_one()
        delegator_users = self._users_from_context(context, "delegator")
        if not delegator_users:
            delegator_users = self._users_from_context(context, "delegate_for")
        if not delegator_users:
            delegator_users = self._users_from_context(context, "resolved_approver")
        if not delegator_users and instance.requester_id:
            delegator_users = instance.requester_id
        if not delegator_users:
            return self.env["res.users"]

        now = fields.Datetime.now()
        domain = [
            ("delegator_id", "in", delegator_users.ids),
            ("company_id", "=", instance.company_id.id),
            ("valid_from", "<=", now),
            ("valid_to", ">=", now),
            "|",
            ("definition_id", "=", False),
            ("definition_id", "=", instance.definition_id.id),
        ]
        delegations = self.env["workflow.delegation.record"].search(domain)
        return delegations.mapped("delegate_id")

    def _create_no_approver_incident(self, instance, context=None):
        """Create the documented no-approver incident."""
        self.ensure_one()
        description = _(
            "No approvers resolved for node '%(node)s' using rule '%(rule)s' (%(source)s)."
        ) % {
            "node": self.node_id,
            "rule": self.name,
            "source": self.resolution_type,
        }
        if self.fallback_type:
            description = _("%(description)s Fallback '%(fallback)s' also returned no users.") % {
                "description": description,
                "fallback": self.fallback_type,
            }

        incident_vals = {
            "instance_id": instance.id,
            "category": "resolution_failure",
            "severity": "high",
            "reason_code": "no_approver_resolved",
            "description": description,
            "correlation_id": instance.correlation_id,
            "company_id": instance.company_id.id,
        }
        incident = self.env["workflow.incident"].create(incident_vals)
        if instance.state != "error_incident":
            instance.write({"state": "error_incident"})
        return incident

    def _create_missing_rule_incident(self, instance, context=None):
        """Create an incident when a node has no approver-resolution rules at all."""
        node_id = (context or {}).get("step_id") or (context or {}).get("node_id") or _("unknown")
        incident_vals = {
            "instance_id": instance.id,
            "category": "resolution_failure",
            "severity": "high",
            "reason_code": "no_approver_resolved",
            "description": _("No approver resolution rules found for node '%(node)s'.") % {"node": node_id},
            "correlation_id": instance.correlation_id,
            "company_id": instance.company_id.id,
        }
        incident = self.env["workflow.incident"].create(incident_vals)
        if instance.state != "error_incident":
            instance.write({"state": "error_incident"})
        return incident

    def _raise_policy_block(self, instance):
        """Block activation when policy rules exclude every active approver."""
        self.ensure_one()
        raise WorkflowSecurityPolicyError(
            _(
                "Approver resolution for node '%(node)s' is blocked by anti-self approval or separation-of-duty policy."
            )
            % {"node": self.node_id or instance.id}
        )

    def _resolve_instance(self, instance_id):
        """Return a workflow.instance record from an ID or record."""
        if isinstance(instance_id, models.BaseModel):
            instance = instance_id
        else:
            instance = self.env["workflow.instance"].browse(instance_id)
        instance = instance.exists()
        if not instance:
            raise WorkflowRuntimeError(_("Workflow instance could not be found for approver resolution."))
        return instance

    def _get_instance_target_record(self, instance):
        """Return the business record referenced by the workflow instance."""
        self.ensure_one()
        if not instance.res_model or not instance.res_id:
            raise WorkflowRuntimeError(_("Workflow instance is missing target record information."))
        target_record = self.env[instance.res_model].browse(instance.res_id).exists()
        if not target_record:
            raise WorkflowRuntimeError(_("Workflow instance target record does not exist."))
        return target_record

    def _validate_field_path(self):
        """Validate field-path syntax that is independent of runtime context."""
        self.ensure_one()
        if any(not segment for segment in self._field_path_segments()):
            raise ValidationError(_("Field Path cannot contain blank path segments."))

    def _field_path_segments(self):
        """Return normalized field path segments."""
        self.ensure_one()
        return [segment.strip() for segment in (self.field_path or "").split(".")]

    def _parse_separation_of_duty_rule(self):
        """Parse the SoD JSON configuration."""
        self.ensure_one()
        if not self.separation_of_duty_rule:
            return {}
        try:
            rule = json.loads(self.separation_of_duty_rule)
        except JSONDecodeError as err:
            raise ValidationError(_("SoD Rule must be valid JSON.")) from err
        if not isinstance(rule, dict):
            raise ValidationError(_("SoD Rule JSON must be an object."))
        return rule

    def _extract_prior_actor_ids(self, prior_decisions):
        """Collect prior actor user IDs from recordsets, dicts, or lists."""
        self.ensure_one()
        if not prior_decisions:
            return set()

        if isinstance(prior_decisions, models.BaseModel):
            if prior_decisions._name == "res.users":
                return set(prior_decisions.ids)
            if "actor_id" in prior_decisions._fields:
                return set(prior_decisions.mapped("actor_id").ids)
            return set()

        if isinstance(prior_decisions, dict):
            prior_decisions = [prior_decisions]

        actor_ids = set()
        for item in prior_decisions:
            if isinstance(item, int):
                actor_ids.add(item)
            elif isinstance(item, dict) and item.get("actor_id"):
                actor_ids.add(item["actor_id"])
        return actor_ids

    def _normalize_user_recordset(self, users, preserve_order=False):
        """Return a deterministic, active-only user recordset."""
        user_recordset = self._coerce_records_to_users(users)
        active_users = user_recordset.filtered("active")
        if not preserve_order:
            ordered_ids = sorted(active_users.ids)
            return self.env["res.users"].browse(ordered_ids)

        ordered_ids = []
        seen_ids = set()
        active_ids = set(active_users.ids)
        for user_id in user_recordset.ids:
            if user_id not in active_ids or user_id in seen_ids:
                continue
            seen_ids.add(user_id)
            ordered_ids.append(user_id)
        return self.env["res.users"].browse(ordered_ids)

    def _coerce_records_to_users(self, records):
        """Convert a recordset or IDs to res.users when possible."""
        if not records:
            return self.env["res.users"]

        if isinstance(records, models.BaseModel):
            if records._name == "res.users":
                return records
            if records._name == "res.partner" and "user_ids" in records._fields:
                return records.mapped("user_ids")
            return self.env["res.users"]

        if isinstance(records, int):
            return self.env["res.users"].browse(records).exists()

        if isinstance(records, list):
            if all(isinstance(item, int) for item in records):
                return self.env["res.users"].browse(records).exists()
            return self.env["res.users"]

        return self.env["res.users"]

    def _users_from_single_group(self, group):
        """Resolve direct and inherited members from one group."""
        self.ensure_one()
        group = group.exists()
        if not group:
            return self.env["res.users"]
        ordered_ids = []
        seen_ids = set()
        for user in group.user_ids.sorted("id"):
            seen_ids.add(user.id)
            ordered_ids.append(user.id)
        for implied_group in self._iter_implied_groups(group):
            for user in implied_group.user_ids.sorted("id"):
                if user.id in seen_ids:
                    continue
                seen_ids.add(user.id)
                ordered_ids.append(user.id)
        return self.env["res.users"].browse(ordered_ids)

    def _users_from_group_recordset(self, groups):
        """Resolve direct and inherited members from multiple groups."""
        self.ensure_one()
        users = self.env["res.users"]
        for group in groups.exists():
            users |= self._users_from_single_group(group)
        return users

    def _iter_implied_groups(self, group, seen_group_ids=None):
        """Yield implied groups depth-first in deterministic order."""
        self.ensure_one()
        seen_group_ids = set(seen_group_ids or set())
        for implied_group in group.implied_ids.sorted("id"):
            if implied_group.id in seen_group_ids:
                continue
            seen_group_ids.add(implied_group.id)
            yield implied_group
            yield from self._iter_implied_groups(implied_group, seen_group_ids=seen_group_ids)

    def _users_from_context(self, context, prefix):
        """Resolve users from common context key variants."""
        self.ensure_one()
        candidates = [
            context.get(f"{prefix}_user_id"),
            context.get(f"{prefix}_user_ids"),
            context.get(f"{prefix}_id"),
            context.get(f"{prefix}_ids"),
        ]
        for candidate in candidates:
            if isinstance(candidate, models.BaseModel):
                return self._coerce_records_to_users(candidate)
            if isinstance(candidate, int):
                return self.env["res.users"].browse(candidate).exists()
            if isinstance(candidate, list) and candidate and all(isinstance(item, int) for item in candidate):
                return self.env["res.users"].browse(candidate).exists()
        return self.env["res.users"]

    def _get_manager_user(self, user):
        """Return a user's manager when HR metadata is available."""
        self.ensure_one()
        user = user.exists()
        if not user:
            return self.env["res.users"]

        if "employee_id" in user._fields and user.employee_id and user.employee_id.parent_id.user_id:
            return user.employee_id.parent_id.user_id

        if "employee_ids" in user._fields:
            manager_users = user.employee_ids.mapped("parent_id.user_id")
            if manager_users:
                return manager_users[:1]

        return self.env["res.users"]
