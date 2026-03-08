from collections import defaultdict

from odoo import _, api, fields, models

from ..exceptions import WorkflowGateBlockedError


class WorkflowApprovalMixin(models.AbstractModel):
    """Mixin for business models participating in approval workflows.

    Provides convenience fields and methods for workflow status
    display and interaction on the target record form view.

    SRS: FR-009  |  SDS: §4 Model Inheritance Strategy
    """

    _name = "workflow.approval.mixin"
    _description = "Workflow Approval Mixin"
    _auto = False

    _approval_state_selection = [
        ("none", "No Workflow"),
        ("pending", "Pending Approval"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    _active_instance_state_selection = [
        ("running", "Running"),
        ("waiting_human", "Waiting - Human"),
        ("waiting_timer", "Waiting - Timer"),
        ("completed_approved", "Approved"),
        ("completed_rejected", "Rejected"),
        ("cancelled", "Cancelled"),
        ("error_incident", "Error / Incident"),
    ]
    _pending_instance_states = (
        "running",
        "waiting_human",
        "waiting_timer",
    )

    workflow_instance_ids = fields.One2many(
        "workflow.instance",
        string="Workflow Instances",
        compute="_compute_workflow_instance_ids",
        readonly=True,
        store=False,
        compute_sudo=True,
    )
    workflow_state = fields.Selection(
        selection=_approval_state_selection,
        string="Workflow State",
        compute="_compute_workflow_state",
        readonly=True,
        store=False,
        compute_sudo=True,
    )
    approval_state = fields.Selection(
        selection=_approval_state_selection,
        string="Approval State",
        compute="_compute_workflow_state",
        readonly=True,
        store=False,
        compute_sudo=True,
    )
    active_instance_id = fields.Many2one(
        "workflow.instance",
        string="Active Workflow Instance",
        compute="_compute_active_instance",
        readonly=True,
        store=False,
        compute_sudo=True,
    )
    active_instance_state = fields.Selection(
        selection=_active_instance_state_selection,
        string="Active Workflow Instance State",
        compute="_compute_active_instance",
        readonly=True,
        store=False,
        compute_sudo=True,
    )

    @api.depends()
    def _compute_workflow_instance_ids(self):
        instance_model = self.env["workflow.instance"].sudo()
        instances_by_record_id = defaultdict(lambda: instance_model.browse())

        if self.ids:
            instances = instance_model.search(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "in", self.ids),
                ],
                order="id desc",
            )
            for instance in instances:
                target_record_id = instance.res_id
                if target_record_id in self.ids:
                    instances_by_record_id[target_record_id] |= instance
        for record in self:
            record.workflow_instance_ids = instances_by_record_id[record.id]

    @api.depends("workflow_instance_ids")
    def _compute_workflow_state(self):
        for record in self:
            approval_state = record._derive_approval_state(record.workflow_instance_ids)
            record.workflow_state = approval_state
            record.approval_state = approval_state

    @api.depends()
    def _compute_active_instance(self):
        if not self:
            return

        mixin_class = type(self)
        pending_states = getattr(
            mixin_class,
            "_pending_instance_states",
            WorkflowApprovalMixin._pending_instance_states,
        )

        instances = (
            self.env["workflow.instance"]
            .sudo()
            .search(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "in", self.ids),
                    ("state", "in", list(pending_states)),
                ],
                order="id desc",
            )
        )

        instances_by_res_id = {}
        for instance in instances:
            # Keep only the latest instance per record (thanks to order="id desc").
            if instance.res_id not in instances_by_res_id:
                instances_by_res_id[instance.res_id] = instance

        for record in self:
            active_instance = instances_by_res_id.get(record.id)
            record.active_instance_id = active_instance or False
            record.active_instance_state = active_instance.state if active_instance else False

    @classmethod
    def _derive_approval_state(cls, instances):
        states = {instance.state for instance in instances if getattr(instance, "state", False)}
        if not states:
            return "none"
        if states.intersection(cls._pending_instance_states):
            return "pending"
        if "completed_rejected" in states:
            return "rejected"
        if states == {"completed_approved"}:
            return "approved"
        return "none"

    def _get_active_workflow_instance(self):
        self.ensure_one()
        mixin_class = type(self)
        pending_states = getattr(
            mixin_class,
            "_pending_instance_states",
            WorkflowApprovalMixin._pending_instance_states,
        )
        return (
            self.env["workflow.instance"]
            .sudo()
            .search(
                [
                    ("res_model", "=", self._name),
                    ("res_id", "=", self.id),
                    ("state", "in", list(pending_states)),
                ],
                order="id desc",
                limit=1,
            )
        )

    def _check_approval_gate(self, action_method, channel="orm"):
        self.ensure_one()
        mixin_class = type(self)
        normalize_gate_state = getattr(
            mixin_class,
            "_normalize_gate_state",
            WorkflowApprovalMixin._normalize_gate_state,
        )
        extract_policy_message = getattr(
            mixin_class,
            "_extract_policy_message",
            WorkflowApprovalMixin._extract_policy_message,
        )
        extract_reason_code = getattr(
            mixin_class,
            "_extract_reason_code",
            WorkflowApprovalMixin._extract_reason_code,
        )
        binding = (
            self.env["workflow.binding"]
            .sudo()
            .search(
                [
                    ("is_active", "=", True),
                    ("target_model", "=", self._name),
                    ("target_action_method", "=", action_method),
                    ("company_id", "in", [self.env.company.id, False]),
                ],
                order="binding_priority desc, id asc",
                limit=1,
            )
        )
        if not binding:
            return {
                "state": "allowed",
                "reason_code": "no_active_binding",
                "policy_message": "",
                "binding_id": False,
            }

        try:
            gate_result = binding.evaluate_gate(
                {
                    "model": self._name,
                    "res_ids": [self.id],
                    "action_method": action_method,
                    "actor_user_id": self.env.user.id,
                    "company_id": self.env.company.id,
                    "channel": channel,
                    "request_id": self.env.context.get("request_id") or False,
                }
            )
        except WorkflowGateBlockedError:
            raise
        except Exception as err:
            raise WorkflowGateBlockedError(_("Workflow gate evaluation failed. Action is blocked.")) from err

        state = normalize_gate_state(gate_result)
        policy_message = extract_policy_message(gate_result)
        result = {
            "state": state,
            "reason_code": extract_reason_code(gate_result),
            "policy_message": policy_message,
            "binding_id": binding.id,
        }
        if state == "blocked":
            raise WorkflowGateBlockedError(policy_message or _("Action is blocked by workflow policy."))
        if state not in {"allowed", "allowed_with_warning"}:
            raise WorkflowGateBlockedError(_("Workflow gate returned invalid state. Action is blocked."))
        return result

    def _workflow_check_gate(self, action_method, channel="orm"):
        return self._check_approval_gate(action_method, channel=channel)

    @staticmethod
    def _normalize_gate_state(gate_result):
        if not isinstance(gate_result, dict):
            return "blocked"
        state = gate_result.get("state") or gate_result.get("decision") or "blocked"
        if state == "allow":
            return "allowed"
        if state == "allow_with_warning":
            return "allowed_with_warning"
        return state

    @staticmethod
    def _extract_reason_code(gate_result):
        if not isinstance(gate_result, dict):
            return "invalid_result"
        return gate_result.get("reason_code") or "gate_evaluated"

    @staticmethod
    def _extract_policy_message(gate_result):
        if not isinstance(gate_result, dict):
            return _("Workflow gate response is invalid.")
        return gate_result.get("policy_message") or gate_result.get("warning_message") or ""
