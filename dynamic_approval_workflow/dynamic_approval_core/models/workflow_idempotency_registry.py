from odoo import api, fields, models


class WorkflowIdempotencyRegistry(models.Model):
    """Dedicated idempotency registry for at-most-once mutations.

    Keyed by ``(operation_type, operation_subject_ref, idempotency_key)``.
    SQL UNIQUE on ``operation_scope_hash`` guarantees at-most-once.

    SDS: §10 Idempotency Pattern  |  ADR-005
    SRS: NFR-016  |  DFR: DFR-10-001..DFR-10-003
    """

    _name = "workflow.idempotency.registry"
    _description = "Workflow Idempotency Registry"
    _order = "created_at_utc desc"

    operation_type = fields.Selection(
        [
            ("start", "Start"),
            ("signal", "Signal"),
            ("complete_task", "Complete Task"),
            ("cancel_instance", "Cancel Instance"),
            ("reassign_task", "Reassign Task"),
            ("execute_callback", "Execute Callback"),
        ],
        required=True,
    )
    operation_subject_ref = fields.Char(
        required=True,
        help="Reference to target record, e.g. workflow.instance,42",
    )
    idempotency_key = fields.Char(
        size=128,
        required=True,
    )
    operation_scope_hash = fields.Char(
        string="Scope Hash (SHA-256)",
        size=64,
        required=True,
        index=True,
    )
    payload_hash = fields.Char(
        string="Payload Hash (SHA-256)",
        size=64,
        required=True,
    )
    result_status = fields.Selection(
        [
            ("success", "Success"),
            ("conflict", "Conflict"),
            ("error", "Error"),
        ],
    )
    result_ref = fields.Char(
        help="Reference to operation outcome record.",
    )
    correlation_id = fields.Char(size=64, index=True)
    causation_id = fields.Char(size=64)
    created_at_utc = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True,
    )
    expires_at_utc = fields.Datetime(
        help="Retention expiry governed by policy. Default 90 days.",
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    _unique_operation_scope_hash = models.Constraint(
        "UNIQUE(operation_scope_hash)",
        "Duplicate idempotency scope detected.",
    )

    @api.model
    def _cron_purge_expired(self):
        """Delete idempotency entries whose retention window has elapsed."""
        expired_entries = self.search(
            [
                ("expires_at_utc", "!=", False),
                ("expires_at_utc", "<=", fields.Datetime.now()),
            ]
        )
        expired_count = len(expired_entries)
        expired_entries.unlink()
        return expired_count
