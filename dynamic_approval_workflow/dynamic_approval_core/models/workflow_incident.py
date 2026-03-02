from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class WorkflowIncident(models.Model):
    """Incident queue with controlled recovery actions.

    State machine: open → triaged → retry_scheduled → resolved → closed_with_exception.

    SDS: §8 Error and Incident Pattern
    SRS: FR-068  |  DFR: DFR-02-014, DFR-04-008, DFR-09-002
    """

    _name = "workflow.incident"
    _description = "Workflow Incident"
    _inherit = ["mail.thread"]
    _order = "opened_at_utc desc"

    name = fields.Char(
        compute="_compute_name",
        store=True,
        readonly=True,
    )
    instance_id = fields.Many2one(
        "workflow.instance",
        readonly=True,
        index=True,
    )
    category = fields.Selection(
        [
            ("callback_failure", "Callback Failure"),
            ("resolution_failure", "Approver Resolution Failure"),
            ("enforcement_failure", "Enforcement Failure"),
            ("timer_failure", "Timer Failure"),
            ("integrity_failure", "Integrity Failure"),
            ("webhook_failure", "Webhook Failure"),
        ],
        required=True,
        readonly=True,
        index=True,
    )
    severity = fields.Selection(
        [
            ("low", "Low"),
            ("medium", "Medium"),
            ("high", "High"),
            ("critical", "Critical"),
        ],
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("open", "Open"),
            ("triaged", "Triaged"),
            ("retry_scheduled", "Retry Scheduled"),
            ("resolved", "Resolved"),
            ("closed_with_exception", "Closed With Exception"),
        ],
        default="open",
        required=True,
        tracking=True,
        index=True,
    )
    reason_code = fields.Char(
        size=64,
        readonly=True,
    )
    description = fields.Text()
    resolution_action = fields.Selection(
        [
            ("retry", "Retry"),
            ("manual_resolution_link", "Manual Resolution"),
            ("close_with_exception", "Close With Exception"),
        ],
    )
    resolution_note = fields.Text()
    opened_at_utc = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True,
    )
    resolved_at_utc = fields.Datetime(readonly=True)
    correlation_id = fields.Char(
        size=64,
        readonly=True,
        index=True,
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    @api.depends("category")
    def _compute_name(self):
        for record in self:
            record.name = (
                f"INC-{record.id or 'new'} [{record.category or ''}]"
            )

    def action_triage(self):
        """Transition from open to triaged."""
        for record in self:
            if record.state != "open":
                raise ValidationError(
                    _("Only open incidents can be triaged.")
                )
            record.write({"state": "triaged"})
        return True

    def action_retry(self):
        """Schedule retry for triaged incident."""
        for record in self:
            if record.state not in ("open", "triaged"):
                raise ValidationError(
                    _("Only open or triaged incidents can be retried.")
                )
            record.write({
                "state": "retry_scheduled",
                "resolution_action": "retry",
            })
        return True

    def action_resolve(self, note=None):
        """Mark incident as resolved.

        Raises ValidationError if incident is not in a resolvable state.
        """
        for record in self:
            if record.state not in ("open", "triaged", "retry_scheduled"):
                raise ValidationError(
                    _("Only open, triaged, or retry-scheduled incidents can be resolved.")
                )
            vals = {
                "state": "resolved",
                "resolved_at_utc": fields.Datetime.now(),
            }
            if note:
                vals["resolution_note"] = note
            record.write(vals)
        return True

    def action_close_with_exception(self, note=None):
        """Close incident with exception — no retry possible.

        Raises ValidationError if incident is already resolved or closed.
        """
        for record in self:
            if record.state in ("resolved", "closed_with_exception"):
                raise ValidationError(
                    _("Resolved or closed incidents cannot be closed with exception.")
                )
            vals = {
                "state": "closed_with_exception",
                "resolution_action": "close_with_exception",
                "resolved_at_utc": fields.Datetime.now(),
            }
            if note:
                vals["resolution_note"] = note
            record.write(vals)
        return True
