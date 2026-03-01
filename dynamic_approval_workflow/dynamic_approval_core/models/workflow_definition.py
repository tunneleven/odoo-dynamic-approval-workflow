from odoo import api, fields, models


class WorkflowDefinition(models.Model):
    """Stable workflow definition header.

    Owns a unique ``definition_key`` per company and links to
    one-or-more immutable ``workflow.definition.version`` records.

    SRS: FR-001, FR-002  |  DFR: DFR-01-001, DFR-01-002
    """

    _name = "workflow.definition"
    _description = "Workflow Definition"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    name = fields.Char(required=True, tracking=True)
    definition_key = fields.Char(
        string="Key",
        required=True,
        copy=False,
        tracking=True,
        help="Human-readable slug [a-z0-9_]+, immutable after first publish.",
    )
    description = fields.Text()
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    tag_ids = fields.Many2many(
        "workflow.definition.tag",
        string="Tags",
    )
    version_ids = fields.One2many(
        "workflow.definition.version",
        "definition_id",
        string="Versions",
    )
    version_count = fields.Integer(
        compute="_compute_version_count",
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "unique_company_key",
            "UNIQUE(company_id, definition_key)",
            "Definition key must be unique per company.",
        ),
    ]

    @api.depends("version_ids")
    def _compute_version_count(self):
        for record in self:
            record.version_count = len(record.version_ids)


class WorkflowDefinitionTag(models.Model):
    """Freeform tags for organising workflow definitions."""

    _name = "workflow.definition.tag"
    _description = "Workflow Definition Tag"
    _order = "name"

    name = fields.Char(required=True)
    color = fields.Integer()
