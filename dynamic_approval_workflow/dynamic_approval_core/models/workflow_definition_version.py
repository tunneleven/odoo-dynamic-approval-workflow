import hashlib

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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
        index=True,
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
        index=True,
    )
    effective_from_utc = fields.Datetime(
        string="Effective From (UTC)",
        index=True,
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
        ondelete="set null",
    )
    source_version_id = fields.Many2one(
        "workflow.definition.version",
        string="Cloned From",
        readonly=True,
        ondelete="set null",
    )
    draft_revision = fields.Integer(
        default=1,
        help="Optimistic-lock revision counter for draft editing.",
    )
    company_id = fields.Many2one(
        related="definition_id.company_id",
        store=True,
        index=True,
        readonly=True,
    )
    compiled_id = fields.Many2one(
        "workflow.definition.compiled",
        string="Compiled Artifact",
        readonly=True,
        ondelete="set null",
    )
    active = fields.Boolean(default=True)

    _unique_version_per_definition = models.Constraint(
        "UNIQUE(definition_id, version)",
        "Version number must be unique per definition.",
    )

    @api.constrains("effective_from_utc", "effective_to_utc")
    def _check_effective_window(self):
        for record in self:
            if (
                record.effective_from_utc
                and record.effective_to_utc
                and record.effective_to_utc <= record.effective_from_utc
            ):
                raise ValidationError(_("Effective To must be later than Effective From."))

    @api.constrains(
        "state",
        "effective_from_utc",
        "published_at_utc",
        "published_by_id",
        "bpmn_hash",
        "version",
    )
    def _check_publish_invariants(self):
        for record in self:
            if record.state != "published":
                continue
            if not record.effective_from_utc:
                raise ValidationError(_("Published versions must define Effective From."))
            if not record.published_at_utc or not record.published_by_id:
                raise ValidationError(_("Published versions must include publish metadata."))
            if not record.bpmn_hash or not record.version:
                raise ValidationError(_("Published versions must include BPMN hash and version number."))

    def _assign_next_version_number(self):
        self.ensure_one()
        latest = self.search(
            [("definition_id", "=", self.definition_id.id), ("version", "!=", False)],
            order="version desc",
            limit=1,
        )
        next_version = (latest.version or 0) + 1
        return next_version

    @staticmethod
    def _compute_bpmn_hash(bpmn_xml):
        xml_value = bpmn_xml or ""
        return hashlib.sha256(xml_value.encode("utf-8")).hexdigest()

    def action_publish(self):
        for record in self:
            if record.state != "draft":
                raise ValidationError(_("Only draft versions can be published."))
            if not record.effective_from_utc:
                raise ValidationError(_("Effective From is required before publishing."))

            vals = {
                "state": "published",
                "published_at_utc": fields.Datetime.now(),
                "published_by_id": self.env.user.id,
                "bpmn_hash": self._compute_bpmn_hash(record.bpmn_xml),
            }
            if not record.version:
                vals["version"] = record._assign_next_version_number()
            record.write(vals)
        return True

    def action_archive(self):
        for record in self:
            if record.state != "published":
                raise ValidationError(_("Only published versions can be archived."))
            record.write({"state": "archived"})
        return True

    def action_clone(self):
        self.ensure_one()
        if self.state != "published":
            raise ValidationError(_("Only published versions can be cloned."))
        values = {
            "definition_id": self.definition_id.id,
            "state": "draft",
            "bpmn_xml": self.bpmn_xml,
            "effective_from_utc": self.effective_from_utc,
            "effective_to_utc": self.effective_to_utc,
            "source_version_id": self.id,
            "draft_revision": 1,
        }
        return self.create(values)

    def write(self, vals):
        immutable_when_published = {
            "bpmn_xml",
            "bpmn_hash",
            "version",
            "published_at_utc",
            "published_by_id",
        }
        result = True
        for record in self:
            write_vals = dict(vals)
            if record.state == "published":
                blocked = [
                    key
                    for key in write_vals
                    if key in immutable_when_published and write_vals.get(key) != record[key]
                ]
                if blocked:
                    raise ValidationError(
                        _(
                            "Published versions are immutable; cannot modify fields: %s"
                        )
                        % ", ".join(sorted(blocked))
                    )
            if record.state == "draft" and any(field_name != "draft_revision" for field_name in write_vals):
                write_vals["draft_revision"] = (record.draft_revision or 0) + 1
            result = super(WorkflowDefinitionVersion, record).write(write_vals) and result
        return result
