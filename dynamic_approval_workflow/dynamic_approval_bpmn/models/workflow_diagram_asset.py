import hashlib

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WorkflowDiagramAsset(models.Model):
    """Canonical BPMN XML source and metadata fingerprint.

    One-to-one relationship with workflow.definition.version.
    Stores the BPMN 2.0 XML and tracks edit history.

    ADR: ADR-003
    DFR: DFR-03-003, DFR-03-005
    """

    _name = "workflow.diagram.asset"
    _description = "Workflow Diagram Asset"
    _order = "id desc"

    definition_version_id = fields.Many2one(
        "workflow.definition.version",
        required=True,
        ondelete="cascade",
        index=True,
        readonly=True,
        string="Version",
    )
    bpmn_xml = fields.Text(
        string="BPMN XML",
        help="Canonical BPMN 2.0 XML",
    )
    bpmn_hash = fields.Char(
        size=64,
        string="BPMN Hash",
        help="SHA-256 of canonical XML",
        index=True,
        readonly=True,
    )
    last_edited_by_id = fields.Many2one(
        "res.users",
        string="Last Edited By",
        readonly=True,
    )
    last_edited_at_utc = fields.Datetime(
        string="Last Edited At",
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        related="definition_version_id.company_id",
        store=True,
        index=True,
        readonly=True,
        string="Company",
    )

    # ---- Business methods ----

    def save_bpmn_xml(self, bpmn_xml, user_id):
        """Save BPMN XML content, recompute hash, and track editor.

        Returns self for chaining.
        """
        self.ensure_one()
        self.write(
            {
                "bpmn_xml": bpmn_xml,
                "bpmn_hash": self._compute_bpmn_hash(bpmn_xml),
                "last_edited_by_id": user_id,
                "last_edited_at_utc": fields.Datetime.now(),
            }
        )
        return self

    def import_bpmn_xml(self, xml_payload):
        """Import BPMN XML from an external payload.

        Returns self for chaining.
        """
        self.ensure_one()
        if not xml_payload:
            raise UserError(_("Cannot import empty BPMN XML."))
        return self.save_bpmn_xml(xml_payload, self.env.uid)

    def export_bpmn_xml(self):
        """Export the stored BPMN XML content.

        Returns the XML string.
        """
        self.ensure_one()
        return self.bpmn_xml or ""

    @api.model
    def _compute_bpmn_hash(self, bpmn_xml):
        """Compute SHA-256 hash of the given BPMN XML string."""
        if not bpmn_xml:
            return False
        return hashlib.sha256(bpmn_xml.encode("utf-8")).hexdigest()
