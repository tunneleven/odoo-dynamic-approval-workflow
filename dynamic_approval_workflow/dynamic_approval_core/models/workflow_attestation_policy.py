from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class WorkflowAttestationPolicy(models.Model):
    """Signature/attestation requirement policy per step.

    SRS: FR-043..FR-046  |  DFR: DFR-06-003
    """

    _name = "workflow.attestation.policy"
    _description = "Workflow Attestation Policy"

    name = fields.Char(required=True)
    definition_version_id = fields.Many2one(
        "workflow.definition.version",
        required=True,
        ondelete="cascade",
        index=True,
    )
    node_id = fields.Char(
        string="BPMN Node ID",
        required=True,
        index=True,
    )
    signature_required = fields.Boolean(default=False)
    legal_human_signature_required = fields.Boolean(
        default=False,
        help="Legal-signature steps cannot permit timeout system attestation.",
    )
    allow_system_attestation_on_timeout = fields.Boolean(
        default=False,
        help="Allow timeout path system attestation where policy permits it.",
    )
    attestation_type = fields.Selection(
        [
            ("human_signature", "Human Signature"),
            ("system_attestation", "System Attestation"),
        ],
    )
    required_evidence_types = fields.Char(
        help="Comma-separated required evidence types for this step.",
    )
    capture_methods = fields.Char(
        help="Comma-separated evidence capture methods for this step.",
    )
    company_id = fields.Many2one(
        related="definition_version_id.company_id",
        store=True,
        index=True,
    )

    @api.constrains("legal_human_signature_required", "allow_system_attestation_on_timeout")
    def _check_legal_blocks_attestation(self):
        for record in self:
            if record.legal_human_signature_required and record.allow_system_attestation_on_timeout:
                raise ValidationError(
                    _("Legal-signature steps cannot allow system attestation on timeout.")
                )
