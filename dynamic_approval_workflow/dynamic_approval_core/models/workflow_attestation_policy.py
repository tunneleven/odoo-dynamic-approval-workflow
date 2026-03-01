from odoo import fields, models


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
    )
    signature_required = fields.Boolean(default=False)
    attestation_type = fields.Selection(
        [
            ("human_signature", "Human Signature"),
            ("system_attestation", "System Attestation"),
        ],
        default="system_attestation",
    )
    company_id = fields.Many2one(
        related="definition_version_id.company_id",
        store=True,
        index=True,
    )
