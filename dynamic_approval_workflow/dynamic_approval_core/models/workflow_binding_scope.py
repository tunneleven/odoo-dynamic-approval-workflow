from odoo import fields, models


class WorkflowBindingScope(models.Model):
    """Per-binding rollout scope (company / group / domain).

    SRS: FR-010, FR-011  |  DFR: DFR-02-001
    """

    _name = "workflow.binding.scope"
    _description = "Workflow Binding Scope"

    binding_id = fields.Many2one(
        "workflow.binding",
        required=True,
        ondelete="cascade",
        index=True,
    )
    scope_type = fields.Selection(
        [
            ("company", "Company"),
            ("group", "Security Group"),
            ("domain", "Record Domain"),
        ],
        required=True,
    )
    scope_company_id = fields.Many2one(
        "res.company",
        string="Company Scope",
    )
    scope_group_id = fields.Many2one(
        "res.groups",
        string="Group Scope",
    )
    scope_domain = fields.Text(
        string="Domain Filter",
        help="Odoo domain expression as JSON string.",
    )
