from odoo import fields, models


class WorkflowApproverResolution(models.Model):
    """Resolves approvers from multiple sources.

    Sources: direct users, groups, roles, requester hierarchy,
    record-field references, and delegate rules.

    SRS: FR-016..FR-021  |  DFR: DFR-05-001..DFR-05-010
    """

    _name = "workflow.approver.resolution"
    _description = "Workflow Approver Resolution Rule"
    _order = "sequence"

    name = fields.Char(required=True)
    definition_version_id = fields.Many2one(
        "workflow.definition.version",
        required=True,
        ondelete="cascade",
        index=True,
    )
    node_id = fields.Char(
        string="BPMN Node ID",
        required=True,
    )
    sequence = fields.Integer(default=10)
    resolution_type = fields.Selection(
        [
            ("user", "Specific Users"),
            ("group", "Security Group"),
            ("role", "Role"),
            ("hierarchy", "Manager Hierarchy"),
            ("field", "Record Field"),
            ("delegate", "Delegate"),
        ],
        required=True,
    )
    user_ids = fields.Many2many(
        "res.users",
        string="Specific Users",
    )
    group_id = fields.Many2one(
        "res.groups",
        string="Security Group",
    )
    field_path = fields.Char(
        help="Dot-separated field path on the business record, e.g. manager_id",
    )
    hierarchy_levels = fields.Integer(
        default=1,
        help="Number of management levels to traverse.",
    )
    quorum_mode = fields.Selection(
        [
            ("all", "All Must Approve"),
            ("any", "Any One"),
            ("quorum", "Quorum Threshold"),
        ],
        default="all",
    )
    quorum_count = fields.Integer(
        help="Absolute minimum approvers (when quorum_mode=quorum).",
    )
    quorum_percentage = fields.Float(
        help="Percentage threshold (when quorum_mode=quorum).",
    )
    anti_self_approval = fields.Boolean(
        default=True,
        help="Prevent requester from approving their own request.",
    )
    company_id = fields.Many2one(
        related="definition_version_id.company_id",
        store=True,
        index=True,
    )
