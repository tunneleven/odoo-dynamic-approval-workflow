from odoo import fields, models


class WorkflowPurgeWizard(models.TransientModel):
    """Operator-triggered purge wizard with legal-hold awareness.

    SDS: §14.2  |  SRS: FR-076
    """

    _name = "workflow.purge.wizard"
    _description = "Workflow Purge Wizard"

    retention_policy_id = fields.Many2one(
        "workflow.retention.policy",
        string="Retention Policy",
        required=True,
    )
    dry_run = fields.Boolean(
        default=True,
        help="Preview without deleting.",
    )
    confirm_text = fields.Char(
        help="Type PURGE to confirm destructive operation.",
    )

    def action_execute(self):
        """Execute purge (stub)."""
        self.ensure_one()
        return {"type": "ir.actions.act_window_close"}
