from odoo import fields, models


class WorkflowNotificationTemplate(models.Model):
    """Configurable notification template per event type.

    SRS: FR-027, FR-028  |  DFR: DFR-08-001
    """

    _name = "workflow.notification.template"
    _description = "Workflow Notification Template"

    name = fields.Char(required=True)
    event_type = fields.Selection(
        [
            ("task_assigned", "Task Assigned"),
            ("task_reminder", "Task Reminder"),
            ("task_escalated", "Task Escalated"),
            ("task_completed", "Task Completed"),
            ("instance_approved", "Instance Approved"),
            ("instance_rejected", "Instance Rejected"),
            ("sla_warning", "SLA Warning"),
            ("sla_breached", "SLA Breached"),
        ],
        required=True,
    )
    channel = fields.Selection(
        [
            ("inbox", "In-App Inbox"),
            ("email", "Email"),
        ],
        required=True,
    )
    mail_template_id = fields.Many2one(
        "mail.template",
        string="Email Template",
    )
    is_active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
