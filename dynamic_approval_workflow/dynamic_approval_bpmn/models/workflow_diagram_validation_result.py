from odoo import fields, models


class WorkflowDiagramValidationResult(models.Model):
    """Structured validation errors and warnings per BPMN element.

    Records are created by the BPMN validation engine and are
    immutable once written. Each row identifies one issue on one
    BPMN element within a definition version.

    SRS: FR-018  |  DFR: DFR-03-006
    """

    _name = "workflow.diagram.validation.result"
    _description = "Workflow Diagram Validation Result"
    _order = "validated_at_utc desc, id desc"

    definition_version_id = fields.Many2one(
        "workflow.definition.version",
        required=True,
        ondelete="cascade",
        index=True,
        readonly=True,
        string="Version",
    )
    element_id = fields.Char(
        size=64,
        required=True,
        readonly=True,
        string="Element ID",
        help="BPMN element ID",
    )
    element_type = fields.Char(
        size=64,
        required=True,
        readonly=True,
        string="Element Type",
        help="BPMN element type",
    )
    xpath_location = fields.Char(
        size=255,
        readonly=True,
        string="XPath",
    )
    error_category = fields.Selection(
        [
            ("structural", "Structural"),
            ("semantic", "Semantic"),
            ("unsupported_element", "Unsupported Element"),
            ("reference_resolution", "Reference Resolution"),
        ],
        required=True,
        readonly=True,
        string="Category",
    )
    error_code = fields.Char(
        size=64,
        required=True,
        readonly=True,
        string="Error Code",
    )
    severity = fields.Selection(
        [
            ("error", "Error"),
            ("warning", "Warning"),
        ],
        required=True,
        default="error",
        readonly=True,
        string="Severity",
    )
    remediation_hint = fields.Text(
        readonly=True,
        string="Remediation",
        help="Human-readable fix suggestion",
    )
    validated_at_utc = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True,
        string="Validated At",
    )
    company_id = fields.Many2one(
        "res.company",
        related="definition_version_id.company_id",
        store=True,
        index=True,
        readonly=True,
        string="Company",
    )
