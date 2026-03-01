from odoo import fields, models


class WorkflowApprovalMixin(models.AbstractModel):
    """Mixin for business models participating in approval workflows.

    Provides convenience fields and methods for workflow status
    display and interaction on the target record form view.

    SRS: FR-009  |  SDS: §4 Model Inheritance Strategy
    """

    _name = "workflow.approval.mixin"
    _description = "Workflow Approval Mixin"

    workflow_instance_ids = fields.One2many(
        "workflow.instance",
        "res_id",
        string="Workflow Instances",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    workflow_state = fields.Selection(
        [
            ("none", "No Workflow"),
            ("pending", "Pending Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        default="none",
        compute="_compute_workflow_state",
        store=False,
    )

    def _compute_workflow_state(self):
        for record in self:
            # Stub — real implementation resolves from active instance
            record.workflow_state = "none"
