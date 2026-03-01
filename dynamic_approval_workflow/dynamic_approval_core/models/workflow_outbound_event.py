from odoo import fields, models


class WorkflowOutboundEvent(models.Model):
    """Persisted outbound webhook event for dispatch.

    Events are persisted before any delivery attempt so the
    delivery worker can retry on failure.

    SDS: §12 External Integration Architecture
    SRS: FR-056..FR-060, FR-083  |  DFR: DFR-08-003..DFR-08-006
    """

    _name = "workflow.outbound.event"
    _description = "Workflow Outbound Event"
    _order = "created_at_utc desc"

    event_type = fields.Char(required=True, index=True)
    schema_version = fields.Char(required=True, default="1.0")
    payload = fields.Text(required=True)
    payload_hash = fields.Char(
        string="Payload Hash",
        size=64,
    )
    signature = fields.Char(
        string="HMAC Signature",
    )
    endpoint_id = fields.Many2one(
        "workflow.webhook.endpoint",
        required=True,
        index=True,
    )
    instance_id = fields.Many2one(
        "workflow.instance",
        index=True,
    )
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("delivered", "Delivered"),
            ("failed", "Failed"),
            ("dead_letter", "Dead Letter"),
        ],
        default="pending",
        required=True,
        index=True,
    )
    attempt_count = fields.Integer(default=0)
    last_error = fields.Text()
    created_at_utc = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True,
        index=True,
    )
    delivered_at_utc = fields.Datetime(readonly=True)
    idempotency_key = fields.Char(size=128, index=True)
    correlation_id = fields.Char(size=64, index=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
