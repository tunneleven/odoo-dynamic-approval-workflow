from odoo import fields, models


class WorkflowTaskTransition(models.Model):
    """Immutable record of a task state transition.

    SRS: FR-022  |  DFR: DFR-04-014
    """

    _name = "workflow.task.transition"
    _description = "Workflow Task Transition"
    _order = "occurred_at_utc"

    task_id = fields.Many2one(
        "workflow.task",
        required=True,
        ondelete="cascade",
        index=True,
    )
    from_status = fields.Char(required=True)
    to_status = fields.Char(required=True)
    actor_id = fields.Many2one("res.users")
    reason = fields.Text()
    occurred_at_utc = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True,
    )
    company_id = fields.Many2one(
        related="task_id.company_id",
        store=True,
        index=True,
    )
