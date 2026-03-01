from odoo import fields, models


class WorkflowConditionRule(models.Model):
    """Routing condition rule for gateway/sequence-flow evaluation.

    SRS: FR-012, FR-013, FR-026  |  DFR: DFR-04-003, DFR-04-006
    """

    _name = "workflow.condition.rule"
    _description = "Workflow Condition Rule"
    _order = "sequence"

    name = fields.Char(required=True)
    definition_version_id = fields.Many2one(
        "workflow.definition.version",
        required=True,
        ondelete="cascade",
        index=True,
    )
    source_node_id = fields.Char(
        string="Source BPMN Node",
        required=True,
    )
    target_node_id = fields.Char(
        string="Target BPMN Node",
        required=True,
    )
    sequence = fields.Integer(default=10)
    condition_type = fields.Selection(
        [
            ("domain", "Domain Expression"),
            ("python", "Python Snippet (Admin Only)"),
        ],
        default="domain",
        required=True,
    )
    domain_filter = fields.Text(
        help="Odoo domain expression as JSON string.",
    )
    python_code = fields.Text(
        help="Admin-only sandboxed Python expression.",
    )
    is_default = fields.Boolean(
        help="Default path when no other condition matches.",
    )
    company_id = fields.Many2one(
        related="definition_version_id.company_id",
        store=True,
        index=True,
    )
