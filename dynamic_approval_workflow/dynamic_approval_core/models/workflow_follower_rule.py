from odoo import fields, models


class WorkflowFollowerRule(models.Model):
    """Auto-follower management rules for workflow-bound records.

    SRS: FR-027  |  SDS: §3.4
    """

    _name = "workflow.follower.rule"
    _description = "Workflow Follower Rule"
    _order = "sequence"

    name = fields.Char(required=True)
    definition_version_id = fields.Many2one(
        "workflow.definition.version",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(default=10)
    follower_type = fields.Selection(
        [
            ("requester", "Requester"),
            ("approver", "Current Approvers"),
            ("group", "Security Group"),
            ("field", "Record Field"),
        ],
        required=True,
    )
    group_id = fields.Many2one("res.groups")
    field_path = fields.Char()
    company_id = fields.Many2one(
        related="definition_version_id.company_id",
        store=True,
        index=True,
    )
