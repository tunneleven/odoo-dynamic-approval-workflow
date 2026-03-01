from odoo import fields, models


class WorkflowAuditEvent(models.Model):
    """Immutable audit trail entry with correlation-based tracing.

    SRS: FR-069, FR-070  |  DFR: DFR-10-004d
    """

    _name = "workflow.audit.event"
    _description = "Workflow Audit Event"
    _order = "occurred_at_utc desc"

    event_type = fields.Char(required=True, index=True)
    actor_id = fields.Many2one("res.users", index=True)
    occurred_at_utc = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True,
        index=True,
    )
    object_ref = fields.Char(
        required=True,
        index=True,
        help="Model reference, e.g. workflow.instance,42",
    )
    payload_hash = fields.Char(size=64)
    payload = fields.Text()
    correlation_id = fields.Char(size=64, index=True)
    causation_id = fields.Char(size=64)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
