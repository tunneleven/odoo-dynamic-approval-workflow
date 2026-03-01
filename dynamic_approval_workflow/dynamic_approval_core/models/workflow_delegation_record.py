from odoo import fields, models


class WorkflowDelegationRecord(models.Model):
    """Delegate approver with validity window.

    SRS: FR-019, FR-024  |  DFR: DFR-05-008
    """

    _name = "workflow.delegation.record"
    _description = "Workflow Delegation Record"
    _order = "valid_from desc"

    delegator_id = fields.Many2one(
        "res.users",
        string="Delegator",
        required=True,
        index=True,
    )
    delegate_id = fields.Many2one(
        "res.users",
        string="Delegate",
        required=True,
        index=True,
    )
    valid_from = fields.Datetime(required=True)
    valid_to = fields.Datetime(required=True)
    is_active = fields.Boolean(
        compute="_compute_is_active",
        store=True,
    )
    definition_id = fields.Many2one(
        "workflow.definition",
        help="Scope delegation to a specific workflow (optional).",
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    def _compute_is_active(self):
        now = fields.Datetime.now()
        for record in self:
            record.is_active = bool(
                record.valid_from
                and record.valid_to
                and record.valid_from <= now <= record.valid_to
            )
