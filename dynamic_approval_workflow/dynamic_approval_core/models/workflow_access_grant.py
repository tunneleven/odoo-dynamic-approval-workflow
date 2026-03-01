from odoo import fields, models


class WorkflowAccessGrant(models.Model):
    """Temporary access grant for approvers on gated records.

    Grant TTL: 5 min – 72 hours (default 24h, per binding).
    Revoked on completion/cancellation/expiry.

    SDS: §11 Access Grant and Caching Strategy
    SRS: FR-051..FR-055  |  DFR: DFR-07-001..DFR-07-005
    """

    _name = "workflow.access.grant"
    _description = "Workflow Access Grant"
    _order = "created_at_utc desc"

    task_id = fields.Many2one(
        "workflow.task",
        required=True,
        ondelete="cascade",
        index=True,
    )
    instance_id = fields.Many2one(
        related="task_id.instance_id",
        store=True,
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        required=True,
        index=True,
    )
    res_model = fields.Char(
        string="Resource Model",
        required=True,
        index=True,
    )
    res_id = fields.Many2oneReference(
        string="Resource ID",
        model_field="res_model",
        required=True,
    )
    state = fields.Selection(
        [
            ("active", "Active"),
            ("revoked", "Revoked"),
            ("expired", "Expired"),
        ],
        default="active",
        required=True,
        index=True,
    )
    expires_at_utc = fields.Datetime(required=True)
    created_at_utc = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True,
    )
    revoked_at_utc = fields.Datetime(readonly=True)
    revoke_reason = fields.Selection(
        [
            ("task_completed", "Task Completed"),
            ("task_reassigned", "Task Reassigned"),
            ("instance_cancelled", "Instance Cancelled"),
            ("ttl_expired", "TTL Expired"),
            ("manual", "Manual Revocation"),
        ],
    )
    company_id = fields.Many2one(
        related="instance_id.company_id",
        store=True,
        index=True,
    )
