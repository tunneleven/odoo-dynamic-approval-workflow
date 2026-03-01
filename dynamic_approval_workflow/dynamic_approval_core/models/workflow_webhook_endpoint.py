from odoo import fields, models


class WorkflowWebhookEndpoint(models.Model):
    """External webhook endpoint configuration.

    SRS: FR-029, FR-056..FR-060  |  DFR: DFR-08-003..DFR-08-006
    """

    _name = "workflow.webhook.endpoint"
    _description = "Workflow Webhook Endpoint"

    name = fields.Char(required=True)
    url = fields.Char(required=True)
    secret = fields.Char(
        help="HMAC-SHA256 signing secret.",
    )
    event_types = fields.Char(
        help="Comma-separated event types to subscribe.",
    )
    is_active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
