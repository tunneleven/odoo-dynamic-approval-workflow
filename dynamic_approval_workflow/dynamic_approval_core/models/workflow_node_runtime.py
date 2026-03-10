from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class WorkflowNodeRuntime(models.Model):
    """Runtime status for a single BPMN node within an instance.

    SRS: FR-021..FR-025  |  DFR: DFR-04-014
    """

    _name = "workflow.node.runtime"
    _description = "Workflow Node Runtime"
    _order = "instance_id, sequence"
    _default_loop_iteration_cap = 5
    _max_loop_iteration = 99
    _immutable_identity_fields = {"instance_id", "node_id", "node_type", "loop_iteration"}
    _node_type_selection = [
        ("start_event", "Start Event"),
        ("end_event", "End Event"),
        ("user_task", "User Task"),
        ("exclusive_gateway", "Exclusive Gateway"),
        ("parallel_gateway", "Parallel Gateway"),
        ("timer_event", "Timer Event"),
    ]
    _state_selection = [
        ("pending", "Pending"),
        ("active", "Active"),
        ("completed", "Completed"),
        ("timed_out", "Timed Out"),
        ("skipped", "Skipped"),
    ]
    _terminal_states = {"completed", "timed_out", "skipped"}
    _managed_timestamp_fields = {"activated_at_utc", "completed_at_utc"}
    _allowed_state_transitions = {
        "pending": {"active", "skipped"},
        "active": {"completed", "timed_out", "skipped"},
        "completed": set(),
        "timed_out": set(),
        "skipped": set(),
    }

    instance_id = fields.Many2one(
        "workflow.instance",
        string="Instance",
        required=True,
        ondelete="cascade",
        index=True,
        readonly=True,
    )
    node_id = fields.Char(
        string="Node ID",
        required=True,
        index=True,
        readonly=True,
        help="BPMN element ID",
    )
    node_type = fields.Selection(
        selection=_node_type_selection,
        string="Node Type",
        required=True,
        readonly=True,
    )
    state = fields.Selection(
        selection=_state_selection,
        string="State",
        default="pending",
        required=True,
        index=True,
    )
    sequence = fields.Integer(string="Sequence", default=10)
    loop_iteration = fields.Integer(
        string="Loop Iteration",
        default=1,
        readonly=True,
        help="Rework loop counter",
    )
    activated_at_utc = fields.Datetime(
        string="Activated At",
        readonly=True,
    )
    completed_at_utc = fields.Datetime(
        string="Completed At",
        readonly=True,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        related="instance_id.company_id",
        store=True,
        index=True,
        readonly=True,
    )

    @api.constrains("loop_iteration")
    def _check_loop_iteration(self):
        """Validate the rework loop counter stays within the documented range."""
        loop_iteration_cap = self._get_loop_iteration_cap()
        for record in self:
            if record.loop_iteration < 1 or record.loop_iteration > loop_iteration_cap:
                raise ValidationError(_("Loop Iteration must be between 1 and %s.") % loop_iteration_cap)

    @api.constrains("state", "activated_at_utc", "completed_at_utc")
    def _check_state_timestamps(self):
        """Keep timestamp invariants aligned with the node state machine."""
        for record in self:
            if record.state == "pending" and (record.activated_at_utc or record.completed_at_utc):
                raise ValidationError(_("Pending node runtimes cannot have activation or completion timestamps."))
            if record.state == "active":
                if not record.activated_at_utc:
                    raise ValidationError(_("Active node runtimes must have an activation timestamp."))
                if record.completed_at_utc:
                    raise ValidationError(_("Active node runtimes cannot have a completion timestamp."))
            if record.state in {"completed", "timed_out"}:
                if not record.activated_at_utc:
                    raise ValidationError(_("Completed or timed-out node runtimes must have an activation timestamp."))
                if not record.completed_at_utc:
                    raise ValidationError(_("Terminal node runtimes must have a completion timestamp."))
            if record.state == "skipped" and not record.completed_at_utc:
                raise ValidationError(_("Skipped node runtimes must have a completion timestamp."))

    def write(self, vals):
        """Apply the documented node state machine and managed timestamps."""
        vals = dict(vals)
        attempted_identity_updates = self._immutable_identity_fields.intersection(vals)
        if attempted_identity_updates:
            raise ValidationError(_("Workflow node runtime identity fields are immutable after creation."))

        provided_timestamp_fields = self._managed_timestamp_fields.intersection(vals)
        if provided_timestamp_fields:
            raise ValidationError(
                _("Activation and completion timestamps are managed by workflow node state transitions.")
            )

        state = vals.get("state")
        if not state:
            return super().write(vals)

        same_state_records = self.filtered(lambda record: record.state == state)
        transition_records = self - same_state_records
        result = True

        if same_state_records:
            same_state_vals = {key: value for key, value in vals.items() if key != "state"}
            if same_state_vals:
                result = super(WorkflowNodeRuntime, same_state_records).write(same_state_vals) and result
            else:
                result = super(WorkflowNodeRuntime, same_state_records).write({}) and result

        if transition_records:
            transition_records._validate_state_transition(state)
            transition_vals = dict(vals)
            timestamp = fields.Datetime.now()
            if state == "active":
                transition_vals.update({"activated_at_utc": timestamp, "completed_at_utc": False})
            elif state in self._terminal_states:
                transition_vals.update({"completed_at_utc": timestamp})
            result = super(WorkflowNodeRuntime, transition_records).write(transition_vals) and result

        return result

    def _validate_state_transition(self, next_state):
        """Validate a requested state change against the SRS transition table."""
        for record in self:
            current_state = record.state
            if current_state == next_state:
                continue
            allowed_states = self._allowed_state_transitions.get(current_state, set())
            if next_state not in allowed_states:
                raise ValidationError(
                    _("Invalid node runtime transition from '%s' to '%s'.") % (current_state, next_state)
                )

    @api.model
    def _get_loop_iteration_cap(self):
        """Return the effective rework loop cap from global configuration."""
        config_value = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param(
                "daw.rework_max_loops",
                default=str(self._default_loop_iteration_cap),
            )
        )
        try:
            loop_iteration_cap = int(config_value)
        except (TypeError, ValueError):
            loop_iteration_cap = self._default_loop_iteration_cap

        return max(1, min(loop_iteration_cap, self._max_loop_iteration))

    @api.model
    def _cron_discover_expired_timers(self):
        """Discover active timer nodes ready for asynchronous execution.

        The authoritative cron contract exists in OMB-04, but OMB-01 does not
        yet define a timer-deadline field on node runtimes. Keep this method
        idempotent and fail-safe until that runtime metadata lands.
        """

        return 0
