import json
from json import JSONDecodeError

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class WorkflowConditionRule(models.Model):
    """Routing condition rule for gateway/sequence-flow evaluation.

    SRS: FR-012, FR-013, FR-026  |  DFR: DFR-04-003, DFR-04-006
    """

    _name = "workflow.condition.rule"
    _description = "Workflow Condition Rule"
    _order = "sequence"

    name = fields.Char(size=128, required=True)
    definition_version_id = fields.Many2one(
        "workflow.definition.version",
        required=True,
        ondelete="cascade",
        index=True,
    )
    source_node_id = fields.Char(
        string="Source BPMN Node",
        size=64,
        required=True,
        index=True,
    )
    target_node_id = fields.Char(
        string="Target BPMN Node",
        size=64,
        required=True,
        index=True,
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
        default=False,
        help="Default path when no other condition matches.",
    )
    company_id = fields.Many2one(
        related="definition_version_id.company_id",
        store=True,
        index=True,
        readonly=True,
    )

    @api.constrains("condition_type", "domain_filter", "python_code")
    def _check_condition_value(self):
        """Validate required values and syntax for the selected condition type."""
        for record in self:
            if record.condition_type == "domain":
                if not record.domain_filter:
                    raise ValidationError(_("Domain filter is required for domain conditions."))
                record._parse_domain_filter()
                continue

            if record.condition_type == "python":
                if not record.python_code:
                    raise ValidationError(_("Python code is required for python conditions."))
                record._validate_python_expression()

    @api.constrains("definition_version_id", "source_node_id", "is_default")
    def _check_single_default_per_source_node(self):
        """Allow at most one default path per source node in a version."""
        for record in self.filtered("is_default"):
            default_count = self.search_count(
                [
                    ("definition_version_id", "=", record.definition_version_id.id),
                    ("source_node_id", "=", record.source_node_id),
                    ("is_default", "=", True),
                ]
            )
            if default_count > 1:
                raise ValidationError(_("Only one default condition is allowed per source node."))

    def _parse_domain_filter(self):
        """Parse and validate domain_filter JSON."""
        self.ensure_one()
        try:
            parsed_domain = json.loads(self.domain_filter or "")
        except JSONDecodeError as err:
            raise ValidationError(_("Domain filter must be valid JSON.")) from err
        if not isinstance(parsed_domain, list):
            raise ValidationError(_("Domain filter JSON must be a list."))
        return parsed_domain

    def _validate_python_expression(self):
        """Ensure python_code is syntactically valid for safe eval."""
        self.ensure_one()
        try:
            compile(self.python_code or "", "<workflow_condition_rule>", "eval")
        except SyntaxError as err:
            raise ValidationError(_("Python condition must be a valid expression.")) from err

    def evaluate(self, record, context):
        """Evaluate the condition against a single business record."""
        self.ensure_one()
        if len(record) != 1:
            raise ValidationError(_("Condition evaluation expects exactly one target record."))

        if self.condition_type == "domain":
            return self._evaluate_domain(record)
        if self.condition_type == "python":
            return self._evaluate_python(record, context or {})
        return False

    def _evaluate_domain(self, record):
        """Evaluate domain_filter against a single record."""
        self.ensure_one()
        parsed_domain = self._parse_domain_filter()
        record_domain = list(parsed_domain) + [("id", "=", record.id)]
        return bool(record.search_count(record_domain))

    def _evaluate_python(self, record, context):
        """Evaluate python_code with a safe context."""
        self.ensure_one()
        try:
            result = safe_eval(
                self.python_code or "False",
                {
                    "record": record,
                    "context": dict(context or {}),
                    "env": record.env,
                },
                mode="eval",
            )
        except Exception as err:
            raise ValidationError(_("Python condition evaluation failed: %s") % err) from err
        return bool(result)
