from odoo import fields, models


class WorkflowArchiveWizard(models.TransientModel):
    """Operator-triggered archival wizard.

    SDS: §14.2
    """

    _name = "workflow.archive.wizard"
    _description = "Workflow Archive Wizard"

    retention_policy_id = fields.Many2one(
        "workflow.retention.policy",
        string="Retention Policy",
        required=True,
    )
    dry_run = fields.Boolean(
        default=True,
        help="Preview without archiving.",
    )

    def action_execute(self):
        """Execute archival (stub)."""
        self.ensure_one()
        return {"type": "ir.actions.act_window_close"}
