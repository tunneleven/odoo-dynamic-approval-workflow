from odoo import fields, models


class WorkflowNotificationLog(models.Model):
    """Delivery log for sent notifications.

    SRS: FR-030  |  DFR: DFR-08-002
    """

    _name = "workflow.notification.log"
    _description = "Workflow Notification Log"
    _order = "sent_at_utc desc"

    instance_id = fields.Many2one(
        "workflow.instance",
        ondelete="cascade",
        index=True,
    )
    task_id = fields.Many2one(
        "workflow.task",
        index=True,
    )
    template_id = fields.Many2one(
        "workflow.notification.template",
    )
    recipient_id = fields.Many2one(
        "res.users",
        index=True,
    )
    channel = fields.Selection(
        [
            ("inbox", "In-App Inbox"),
            ("email", "Email"),
        ],
        required=True,
    )
    state = fields.Selection(
        [
            ("sent", "Sent"),
            ("failed", "Failed"),
        ],
        required=True,
    )
    error_message = fields.Text()
    sent_at_utc = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True,
    )
    company_id = fields.Many2one(
        related="instance_id.company_id",
        store=True,
        index=True,
    )
