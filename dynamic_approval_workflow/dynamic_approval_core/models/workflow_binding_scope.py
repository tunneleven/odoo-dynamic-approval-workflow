import json
from json import JSONDecodeError

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class WorkflowBindingScope(models.Model):
    """Rollout scope values for binding precedence evaluation."""

    _name = "workflow.binding.scope"
    _description = "Workflow Binding Scope"

    binding_id = fields.Many2one(
        "workflow.binding",
        required=True,
        ondelete="cascade",
        index=True,
    )
    scope_type = fields.Selection(
        [
            ("company", "Company"),
            ("group", "Security Group"),
            ("domain", "Record Domain"),
        ],
        required=True,
    )
    scope_company_id = fields.Many2one("res.company")
    scope_group_id = fields.Many2one("res.groups")
    scope_domain = fields.Text(
        help="JSON domain expression.",
    )
    company_id = fields.Many2one(
        related="binding_id.company_id",
        store=True,
        index=True,
        readonly=True,
    )

    @api.constrains("scope_type", "scope_company_id", "scope_group_id", "scope_domain", "binding_id")
    def _check_scope_value_required(self):
        for record in self:
            if record.scope_type == "company" and not record.scope_company_id:
                raise ValidationError(_("Scope company is required for company scope type."))
            if record.scope_type == "group" and not record.scope_group_id:
                raise ValidationError(_("Scope group is required for group scope type."))
            if record.scope_type == "domain":
                if not record.scope_domain:
                    raise ValidationError(_("Scope domain is required for domain scope type."))
                parsed_domain = record._parse_scope_domain()
                record._validate_scope_domain_fields(parsed_domain)

            if record.scope_type != "company" and record.scope_company_id:
                raise ValidationError(_("Scope company can only be used with scope type 'company'."))
            if record.scope_type != "group" and record.scope_group_id:
                raise ValidationError(_("Scope group can only be used with scope type 'group'."))
            if record.scope_type != "domain" and record.scope_domain:
                raise ValidationError(_("Scope domain can only be used with scope type 'domain'."))

    def _parse_scope_domain(self):
        self.ensure_one()
        try:
            parsed = json.loads(self.scope_domain or "")
        except JSONDecodeError as err:
            raise ValidationError(_("Scope domain must be valid JSON.")) from err

        if not isinstance(parsed, list):
            raise ValidationError(_("Scope domain JSON must be a list expression."))
        return parsed

    def _validate_scope_domain_fields(self, domain_expression):
        self.ensure_one()
        target_model = self.binding_id.target_model
        if not (bool(target_model) and target_model in self.env):
            raise ValidationError(_("Cannot validate scope domain: target model '%s' is not installed.") % target_model)

        model_fields = self.env[target_model]._fields
        for field_name in self._iter_domain_field_names(domain_expression):
            root_field = field_name.split(".", 1)[0]
            if root_field not in model_fields:
                raise ValidationError(
                    _("Scope domain references unknown field '%s' on model '%s'.") % (field_name, target_model)
                )

    @classmethod
    def _iter_domain_field_names(cls, expression):
        if isinstance(expression, list):
            if expression and isinstance(expression[0], str) and expression[0] not in {"&", "|", "!"}:
                yield expression[0]
                return
            for item in expression:
                yield from cls._iter_domain_field_names(item)

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        if not self.env.context.get("skip_binding_revision_increment"):
            records.mapped("binding_id")._increment_config_revision()
        return records

    def write(self, vals):
        bindings_before = self.mapped("binding_id")
        result = super().write(vals)
        if not self.env.context.get("skip_binding_revision_increment"):
            (bindings_before | self.mapped("binding_id"))._increment_config_revision()
        return result

    def unlink(self):
        bindings = self.mapped("binding_id")
        result = super().unlink()
        if not self.env.context.get("skip_binding_revision_increment"):
            bindings._increment_config_revision()
        return result
