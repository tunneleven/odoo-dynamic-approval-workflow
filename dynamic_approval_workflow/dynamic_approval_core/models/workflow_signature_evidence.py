from odoo import fields, models


class WorkflowSignatureEvidence(models.Model):
    """Immutable evidence artifact for approval signatures.

    Evidence records are **immutable** after creation:
    ``write`` blocks immutable fields, ``unlink`` is blocked entirely.

    SDS: §13 Signature and Evidence Storage
    SRS: FR-043..FR-046, FR-084, FR-085, FR-096
    DFR: DFR-06-001..DFR-06-007
    """

    _name = "workflow.signature.evidence"
    _description = "Workflow Signature Evidence"
    _order = "created_at_utc desc"

    task_id = fields.Many2one(
        "workflow.task",
        required=True,
        ondelete="restrict",
        index=True,
    )
    instance_id = fields.Many2one(
        related="task_id.instance_id",
        store=True,
        index=True,
    )
    signer_id = fields.Many2one(
        "res.users",
        string="Signer",
        required=True,
    )
    evidence_type = fields.Selection(
        [
            ("human_signature", "Human Signature"),
            ("system_attestation", "System Attestation"),
        ],
        required=True,
    )
    evidence_hash = fields.Char(
        string="Evidence Hash (SHA-256)",
        size=64,
        readonly=True,
        required=True,
    )
    attachment_id = fields.Many2one(
        "ir.attachment",
        string="Signature Image",
        ondelete="restrict",
    )
    policy_id = fields.Many2one(
        "workflow.attestation.policy",
    )
    superseded_by_id = fields.Many2one(
        "workflow.signature.evidence",
        string="Superseded By",
        readonly=True,
    )
    supersede_reason = fields.Text(readonly=True)
    created_at_utc = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True,
    )
    company_id = fields.Many2one(
        related="task_id.company_id",
        store=True,
        index=True,
    )
