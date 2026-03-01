from odoo import fields, models


class WorkflowDecisionEvent(models.Model):
    """User or system decision input that may advance runtime.

    SRS: FR-023  |  DFR: DFR-04-001
    """

    _name = "workflow.decision.event"
    _description = "Workflow Decision Event"
    _order = "occurred_at_utc desc"

    instance_id = fields.Many2one(
        "workflow.instance",
        required=True,
        ondelete="cascade",
        index=True,
    )
    task_id = fields.Many2one(
        "workflow.task",
        index=True,
    )
    decision = fields.Selection(
        [
            ("approve", "Approve"),
            ("reject", "Reject"),
            ("request_change", "Request Change"),
            ("delegate", "Delegate"),
            ("escalate", "Escalate"),
            ("auto_approve", "Auto-Approve (Timeout)"),
            ("auto_reject", "Auto-Reject (Timeout)"),
        ],
        required=True,
    )
    actor_id = fields.Many2one(
        "res.users",
        string="Actor",
        required=True,
        index=True,
    )
    comment = fields.Text()
    occurred_at_utc = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True,
    )
    idempotency_key = fields.Char(size=128, index=True)
    correlation_id = fields.Char(size=64, index=True)
    company_id = fields.Many2one(
        related="instance_id.company_id",
        store=True,
        index=True,
    )
