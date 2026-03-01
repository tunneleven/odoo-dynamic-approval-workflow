from odoo import api, fields, models


class WorkflowDefinitionVersion(models.Model):
    """Immutable published version of a workflow definition.

    Lifecycle: draft → published → archived.
    Published versions are immutable in structure, policies, and compiled
    artifacts.

    SRS: FR-003..FR-006  |  DFR: DFR-01-003..DFR-01-011
    """

    _name = "workflow.definition.version"
    _description = "Workflow Definition Version"
    _inherit = ["mail.thread"]
    _order = "definition_id, version desc"

    definition_id = fields.Many2one(
        "workflow.definition",
        required=True,
        ondelete="cascade",
        index=True,
    )
    version = fields.Integer(
        string="Version Number",
        readonly=True,
        help="Monotonic integer assigned at publish time.",
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("published", "Published"),
            ("archived", "Archived"),
        ],
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )
    bpmn_xml = fields.Text(
        string="BPMN XML",
        help="Canonical BPMN XML source of truth.",
    )
    bpmn_hash = fields.Char(
        string="BPMN Hash",
        size=64,
        readonly=True,
        help="SHA-256 of canonical BPMN XML.",
    )
    effective_from_utc = fields.Datetime(
        string="Effective From (UTC)",
    )
    effective_to_utc = fields.Datetime(
        string="Effective To (UTC)",
    )
    published_at_utc = fields.Datetime(
        string="Published At (UTC)",
        readonly=True,
    )
    published_by_id = fields.Many2one(
        "res.users",
        string="Published By",
        readonly=True,
    )
    source_version_id = fields.Many2one(
        "workflow.definition.version",
        string="Cloned From",
        readonly=True,
    )
    draft_revision = fields.Integer(
        default=1,
        help="Optimistic-lock revision counter for draft editing.",
    )
    company_id = fields.Many2one(
        related="definition_id.company_id",
        store=True,
        index=True,
    )
    compiled_id = fields.Many2one(
        "workflow.definition.compiled",
        string="Compiled Artifact",
        readonly=True,
    )
    active = fields.Boolean(default=True)

    @api.model_create_multi
    def create(self, vals_list):
        return super().create(vals_list)
