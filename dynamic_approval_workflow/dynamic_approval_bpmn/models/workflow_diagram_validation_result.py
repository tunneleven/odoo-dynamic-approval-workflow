from odoo import fields, models


class WorkflowDiagramValidationResult(models.Model):
    """Structured validation result for BPMN diagram elements.

    Returns ``element_id``, ``error_category``, ``error_code``,
    and ``remediation_hint`` per SDS §5.5.

    SRS: FR-018  |  DFR: DFR-03-005
    """

    _name = "workflow.diagram.validation.result"
    _description = "Workflow Diagram Validation Result"
    _order = "create_date desc"

    definition_version_id = fields.Many2one(
        "workflow.definition.version",
        required=True,
        ondelete="cascade",
        index=True,
    )
    element_id = fields.Char(
        string="BPMN Element ID",
        required=True,
    )
    element_type = fields.Char()
    xpath_location = fields.Char()
    error_category = fields.Selection(
        [
            ("structural", "Structural"),
            ("semantic", "Semantic"),
            ("unsupported", "Unsupported Element"),
            ("policy", "Policy Violation"),
        ],
        required=True,
    )
    error_code = fields.Char(required=True)
    message = fields.Text()
    remediation_hint = fields.Text()
    severity = fields.Selection(
        [
            ("error", "Error"),
            ("warning", "Warning"),
            ("info", "Info"),
        ],
        default="error",
    )
    company_id = fields.Many2one(
        related="definition_version_id.company_id",
        store=True,
        index=True,
    )
