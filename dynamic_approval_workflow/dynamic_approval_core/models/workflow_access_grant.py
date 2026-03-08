from odoo import _, api, fields, models


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

    def _create_lifecycle_logs(self, event_type, reason):
        """Persist immutable lifecycle log entries for the grant recordset."""
        log_model = self.env["workflow.access.grant.log"]
        for record in self:
            log_model.create(
                {
                    "grant_id": record.id,
                    "event_type": event_type,
                    "reason": reason,
                }
            )

    @api.model
    def _cron_expire_grants(self):
        """Expire active grants that have reached their configured TTL."""
        now = fields.Datetime.now()
        expired_grants = self.search(
            [
                ("state", "=", "active"),
                ("expires_at_utc", "<=", now),
            ]
        )
        if not expired_grants:
            return 0

        expired_grants.write(
            {
                "state": "expired",
                "revoked_at_utc": now,
                "revoke_reason": "ttl_expired",
            }
        )
        expired_grants._create_lifecycle_logs(
            "expired",
            _("Grant expired after TTL elapsed."),
        )
        return len(expired_grants)

    @api.model
    def _cron_reconcile_orphan_grants(self):
        """Revoke grants whose driving task or instance is no longer actionable."""
        orphan_grants = self.search(
            [
                ("state", "=", "active"),
                "|",
                ("task_id.status", "=", "completed"),
                (
                    "instance_id.state",
                    "in",
                    ("completed_approved", "completed_rejected", "cancelled"),
                ),
            ]
        )
        if not orphan_grants:
            return 0

        now = fields.Datetime.now()
        for grant in orphan_grants:
            revoke_reason = "instance_cancelled" if grant.instance_id.state == "cancelled" else "task_completed"
            grant.write(
                {
                    "state": "revoked",
                    "revoked_at_utc": now,
                    "revoke_reason": revoke_reason,
                }
            )
            grant._create_lifecycle_logs(
                "reconciled",
                _("Grant revoked by orphan-grant reconciliation."),
            )
        return len(orphan_grants)
