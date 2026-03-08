from odoo import api, fields, models


class WorkflowTask(models.Model):
    """Actionable approval task for an active step.

    SRS: FR-022..FR-026  |  DFR: DFR-05-001..DFR-05-013
    """

    _name = "workflow.task"
    _description = "Workflow Approval Task"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"

    name = fields.Char(required=True)
    instance_id = fields.Many2one(
        "workflow.instance",
        required=True,
        ondelete="cascade",
        index=True,
    )
    node_runtime_id = fields.Many2one(
        "workflow.node.runtime",
        index=True,
    )
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("assigned", "Assigned"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
            ("escalated", "Escalated"),
        ],
        default="pending",
        required=True,
        tracking=True,
        index=True,
    )
    decision = fields.Selection(
        [
            ("approve", "Approved"),
            ("reject", "Rejected"),
            ("request_change", "Request Change"),
        ],
    )
    assignee_user_id = fields.Many2one(
        "res.users",
        string="Assignee",
        index=True,
        tracking=True,
    )
    assignee_group_id = fields.Many2one(
        "res.groups",
        string="Assignee Group",
        index=True,
    )
    delegated_from_id = fields.Many2one(
        "res.users",
        string="Delegated From",
    )
    sla_due_at_utc = fields.Datetime(
        string="SLA Deadline (UTC)",
    )
    is_overdue = fields.Boolean(
        compute="_compute_is_overdue",
        store=True,
    )
    completed_at_utc = fields.Datetime(readonly=True)
    comment = fields.Text()
    company_id = fields.Many2one(
        related="instance_id.company_id",
        store=True,
        index=True,
    )

    @api.depends("sla_due_at_utc", "status")
    def _compute_is_overdue(self):
        """Mark non-terminal tasks that have crossed their SLA deadline."""
        now = fields.Datetime.now()
        for task in self:
            task.is_overdue = bool(
                task.sla_due_at_utc and task.status not in ("completed", "cancelled") and task.sla_due_at_utc < now
            )

    @api.model
    def _cron_check_sla(self):
        """Refresh overdue markers for tasks with SLA deadlines."""
        tracked_tasks = self.search(
            [
                ("sla_due_at_utc", "!=", False),
                ("status", "not in", ("completed", "cancelled")),
            ]
        )
        tracked_tasks._compute_is_overdue()
        return len(tracked_tasks.filtered("is_overdue"))

    @api.model
    def _cron_check_deadlines(self):
        """Scan overdue tasks for deadline-driven follow-up actions."""
        return self._cron_check_sla()
