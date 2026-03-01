from odoo import fields, models


class WorkflowIncident(models.Model):
    """Runtime/configuration error requiring operator intervention.

    SDS: §8 Error and Incident Pattern
    SRS: FR-068  |  DFR: DFR-09-002, DFR-10-004c
    """

    _name = "workflow.incident"
    _description = "Workflow Incident"
    _inherit = ["mail.thread"]
    _order = "opened_at_utc desc"

    name = fields.Char(
        compute="_compute_name",
        store=True,
    )
    instance_id = fields.Many2one(
        "workflow.instance",
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
    )
    state = fields.Selection(
        [
            ("open", "Open"),
            ("in_progress", "In Progress"),
            ("resolved", "Resolved"),
            ("closed", "Closed"),
        ],
        default="open",
        required=True,
        tracking=True,
        index=True,
    )
    reason_code = fields.Char()
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
    correlation_id = fields.Char(size=64, index=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    def _compute_name(self):
        for record in self:
            record.name = (
                f"INC-{record.id or 'new'} [{record.category or ''}]"
            )
