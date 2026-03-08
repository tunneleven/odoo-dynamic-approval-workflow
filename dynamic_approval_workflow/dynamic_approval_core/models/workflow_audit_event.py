import hashlib
import json

from odoo import _, api, fields, models

from ..exceptions import WorkflowIntegrityError


class WorkflowAuditEvent(models.Model):
    """Immutable, append-only audit event timeline.

    Events are never modified or deleted after creation.

    SRS: FR-068, FR-095, NFR-010  |  DFR: DFR-07-007, DFR-07-010
    """

    _name = "workflow.audit.event"
    _description = "Workflow Audit Event"
    _order = "occurred_at_utc desc"

    event_type = fields.Char(
        size=128,
        required=True,
        readonly=True,
        index=True,
    )
    actor_id = fields.Many2one(
        "res.users",
        readonly=True,
        index=True,
    )
    occurred_at_utc = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True,
        index=True,
    )
    object_ref = fields.Char(
        size=255,
        required=True,
        readonly=True,
        index=True,
        help="Model reference, e.g. workflow.instance,42",
    )
    payload_hash = fields.Char(
        size=64,
        readonly=True,
    )
    payload = fields.Text(readonly=True)
    correlation_id = fields.Char(
        size=64,
        readonly=True,
        index=True,
    )
    causation_id = fields.Char(
        size=64,
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        readonly=True,
        index=True,
    )

    # SECURITY: Audit events are immutable evidence. Model-level write is
    # blocked even if ACLs grant perm_write to any group. Any change to
    # this behaviour must be coordinated with ir.model.access.csv so that
    # security remains fail-closed and ACLs do not contradict model logic.
    def write(self, vals):
        """Blocked — audit events are immutable."""
        raise WorkflowIntegrityError(_("Audit events are immutable and cannot be modified."))

    # SECURITY: Deletion is blocked at the model layer to guarantee that
    # audit evidence is append-only. ACL perm_unlink must not be relied
    # upon to allow deletions for this model.
    def unlink(self):
        """Blocked — audit events are never deleted."""
        raise WorkflowIntegrityError(_("Audit events are immutable and cannot be deleted."))

    @api.model
    def log_event(
        self,
        event_type,
        object_ref,
        payload=None,
        correlation_id=None,
        causation_id=None,
    ):
        """Create an immutable audit event record.

        Returns the created record.
        """
        vals = {
            "event_type": event_type,
            "object_ref": object_ref,
            "actor_id": self.env.user.id,
        }
        if payload is not None:
            payload_str = json.dumps(payload, sort_keys=True, default=str)
            vals["payload"] = payload_str
            vals["payload_hash"] = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()
        if correlation_id:
            vals["correlation_id"] = correlation_id
        if causation_id:
            vals["causation_id"] = causation_id
        return self.create(vals)
