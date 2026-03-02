from odoo import _, api, fields, models

from ..exceptions import WorkflowError


class WorkflowDefinitionCompiled(models.Model):
    """Deterministic compiled runtime artifact derived from canonical BPMN XML.

    Generated during workflow version publish; keyed by ``bpmn_hash``.
    Immutable once created — ``write()`` and ``unlink()`` are blocked.

    DFR: DFR-01-005, DFR-03-003
    SRS: FR-015
    """

    _name = "workflow.definition.compiled"
    _description = "Workflow Definition Compiled Artifact"

    bpmn_hash = fields.Char(
        string="BPMN Hash",
        size=64,
        required=True,
        readonly=True,
        index=True,
        help="SHA-256 of source XML",
    )
    compiled_data = fields.Text(
        string="Compiled Data",
        required=True,
        readonly=True,
        help="JSON runtime artifact",
    )
    node_count = fields.Integer(
        string="Node Count",
        readonly=True,
    )
    gateway_count = fields.Integer(
        string="Gateway Count",
        readonly=True,
    )
    compiled_at_utc = fields.Datetime(
        string="Compiled At",
        readonly=True,
        default=fields.Datetime.now,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    _unique_hash_company = models.Constraint(
        "UNIQUE(bpmn_hash, company_id)",
        "Compiled artifact must be unique per BPMN hash and company.",
    )

    def write(self, vals):
        """Block all modifications — compiled artifacts are immutable after creation."""
        raise WorkflowError(
            _("Compiled workflow artifacts are immutable and cannot be modified.")
        )

    @api.ondelete(at_uninstall=False)
    def _unlink_except_immutable(self):
        """Block deletion — compiled artifacts are immutable after creation."""
        raise WorkflowError(
            _("Compiled workflow artifacts are immutable and cannot be deleted.")
        )
