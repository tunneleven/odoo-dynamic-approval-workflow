from odoo import _, fields, models

from ..exceptions import WorkflowIntegrityError


class WorkflowDecisionEvent(models.Model):
    """Immutable decision record for approval workflow audit trail.

    Decision events are **immutable** after creation: ``write()`` and
    ``unlink()`` are blocked at the model layer to guarantee an
    append-only audit stream.

    SRS: FR-029, FR-030  |  DFR: DFR-04-001, DFR-04-003
    """

    _name = "workflow.decision.event"
    _description = "Workflow Decision Event"
    _order = "occurred_at_utc desc"

    instance_id = fields.Many2one(
        "workflow.instance",
        required=True,
        ondelete="cascade",
        readonly=True,
        index=True,
        string="Instance",
    )
    task_id = fields.Many2one(
        "workflow.task",
        ondelete="set null",
        readonly=True,
        index=True,
        string="Task",
    )
    decision = fields.Selection(
        [
            ("approve", "Approve"),
            ("reject", "Reject"),
            ("request_change", "Request Change"),
            ("delegate", "Delegate"),
            ("escalate", "Escalate"),
            ("auto_approve", "Auto-Approve (Timeout)"),
            ("auto_reject", "Auto-Reject (Timeout)"),
        ],
        required=True,
        readonly=True,
        string="Decision",
    )
    actor_id = fields.Many2one(
        "res.users",
        required=True,
        ondelete="restrict",
        readonly=True,
        index=True,
        string="Actor",
    )
    comment = fields.Text(
        string="Comment",
    )
    occurred_at_utc = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True,
        string="Occurred At",
    )
    idempotency_key = fields.Char(
        size=128,
        readonly=True,
        index=True,
        string="Idempotency Key",
    )
    correlation_id = fields.Char(
        size=64,
        readonly=True,
        index=True,
        string="Correlation ID",
    )
    company_id = fields.Many2one(
        "res.company",
        related="instance_id.company_id",
        store=True,
        readonly=True,
        index=True,
        string="Company",
    )

    # SECURITY: Decision events are immutable audit evidence. Model-level
    # write is blocked even if ACLs grant perm_write to any group. This
    # guarantees the decision trail cannot be retroactively altered. Any
    # change to this behaviour must be coordinated with ir.model.access.csv
    # so that security remains fail-closed.
    def write(self, vals):
        """Blocked — decision events are immutable after creation."""
        raise WorkflowIntegrityError(_("Decision events are immutable and cannot be modified."))

    # SECURITY: Deletion is blocked at the model layer to guarantee that
    # the decision audit trail is append-only. ACL perm_unlink must not
    # be relied upon to allow deletions for this model.
    def unlink(self):
        """Blocked — decision events are never deleted."""
        raise WorkflowIntegrityError(_("Decision events are immutable and cannot be deleted."))
