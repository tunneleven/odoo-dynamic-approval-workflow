from odoo import fields, models


class WorkflowAccessGrantLog(models.Model):
    """Immutable audit log for grant lifecycle events.

    SDS: §11.3 Cache Invalidation
    SRS: FR-055  |  DFR: DFR-07-004
    """

    _name = "workflow.access.grant.log"
    _description = "Workflow Access Grant Log"
    _order = "occurred_at_utc desc"

    grant_id = fields.Many2one(
        "workflow.access.grant",
        required=True,
        ondelete="cascade",
        index=True,
    )
    event_type = fields.Selection(
        [
            ("created", "Created"),
            ("revoked", "Revoked"),
            ("expired", "Expired"),
            ("reconciled", "Reconciled"),
        ],
        required=True,
    )
    actor_id = fields.Many2one("res.users")
    reason = fields.Text()
    occurred_at_utc = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True,
    )
    company_id = fields.Many2one(
        related="grant_id.company_id",
        store=True,
        index=True,
    )
