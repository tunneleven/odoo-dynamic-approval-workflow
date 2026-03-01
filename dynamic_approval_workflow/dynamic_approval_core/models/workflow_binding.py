from odoo import fields, models


class WorkflowBinding(models.Model):
    """Binds a published workflow definition to a target model/action.

    Supports enforcement modes: ``orm_enforced``, ``hybrid``, ``ui_only``.

    SRS: FR-007..FR-012, FR-090..FR-095
    DFR: DFR-02-001..DFR-02-015
    """

    _name = "workflow.binding"
    _description = "Workflow Binding"
    _inherit = ["mail.thread"]
    _order = "target_model, target_action_method"

    name = fields.Char(required=True, tracking=True)
    definition_id = fields.Many2one(
        "workflow.definition",
        required=True,
        ondelete="restrict",
        index=True,
    )
    target_model = fields.Char(
        required=True,
        index=True,
        help="Technical model name, e.g. sale.order",
    )
    target_action_method = fields.Char(
        required=True,
        index=True,
        help="Method name to intercept, e.g. action_confirm",
    )
    enforcement_mode = fields.Selection(
        [
            ("orm_enforced", "ORM Enforced"),
            ("hybrid", "Hybrid"),
            ("ui_only", "UI Only"),
        ],
        default="orm_enforced",
        required=True,
        tracking=True,
    )
    compliance_critical = fields.Boolean(
        default=False,
        help="When True, ui_only enforcement is forbidden.",
    )
    callback_model = fields.Char(
        help="Post-approval callback target model.",
    )
    callback_method = fields.Char(
        help="Post-approval callback target method.",
    )
    is_active = fields.Boolean(
        string="Active Binding",
        default=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    scope_ids = fields.One2many(
        "workflow.binding.scope",
        "binding_id",
        string="Rollout Scopes",
    )

    _sql_constraints = [
        (
            "unique_model_action_company",
            "UNIQUE(target_model, target_action_method, company_id)",
            "Only one active binding per model/action/company.",
        ),
    ]
