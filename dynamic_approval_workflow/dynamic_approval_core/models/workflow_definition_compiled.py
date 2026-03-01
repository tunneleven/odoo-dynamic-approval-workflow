from odoo import fields, models


class WorkflowDefinitionCompiled(models.Model):
    """Deterministic compiled runtime artifact derived from BPMN XML.

    Generated during publish; keyed by canonical ``bpmn_hash``.
    Immutable once created.

    SRS: FR-015  |  DFR: DFR-03-003
    """

    _name = "workflow.definition.compiled"
    _description = "Workflow Definition Compiled Artifact"

    bpmn_hash = fields.Char(
        string="Source BPMN Hash",
        size=64,
        required=True,
        index=True,
    )
    compiled_data = fields.Text(
        string="Compiled Metadata (JSON)",
        required=True,
        help="Deterministic runtime artifact in JSON format.",
    )
    node_count = fields.Integer()
    gateway_count = fields.Integer()
    compiled_at_utc = fields.Datetime(
        string="Compiled At (UTC)",
        readonly=True,
        default=fields.Datetime.now,
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    _sql_constraints = [
        (
            "unique_bpmn_hash_company",
            "UNIQUE(bpmn_hash, company_id)",
            "Compiled artifact must be unique per BPMN hash and company.",
        ),
    ]
