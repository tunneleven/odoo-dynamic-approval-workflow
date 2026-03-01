import re

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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
    _definition_key_regex = re.compile(r"^[a-z][a-z0-9_]{2,63}$")

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

    _unique_company_key = models.Constraint(
        "UNIQUE(company_id, definition_key)",
        "Definition key must be unique per company.",
    )

    @api.depends("version_ids")
    def _compute_version_count(self):
        for record in self:
            record.version_count = len(record.version_ids)

    @api.constrains("definition_key")
    def _check_definition_key_format(self):
        for record in self:
            if not self._definition_key_regex.fullmatch(record.definition_key or ""):
                raise ValidationError(
                    _(
                        "Definition key must match ^[a-z][a-z0-9_]{2,63}$ "
                        "(lowercase letters, digits, underscores)."
                    )
                )

    def unlink(self):
        for record in self:
            if record.version_ids.filtered(lambda version: version.state == "published"):
                raise ValidationError(_("Cannot delete a workflow definition with published versions."))
        return super().unlink()


class WorkflowDefinitionTag(models.Model):
    """Freeform tags for organising workflow definitions."""

    _name = "workflow.definition.tag"
    _description = "Workflow Definition Tag"
    _order = "name"

    name = fields.Char(required=True)
    color = fields.Integer(default=0)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    _unique_name_company = models.Constraint(
        "UNIQUE(name, company_id)",
        "Tag name must be unique per company.",
    )
