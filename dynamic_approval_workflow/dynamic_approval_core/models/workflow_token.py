from odoo import fields, models


class WorkflowToken(models.Model):
    """Branch progress marker through sequence flows.

    Tokens are **never deleted** — state transitions only
    (``active`` → ``consumed`` / ``cancelled``).

    SDS: §6.6 Token Management
    SRS: FR-022, FR-024  |  DFR: DFR-04-013
    """

    _name = "workflow.token"
    _description = "Workflow Token"
    _order = "instance_id, create_date"

    instance_id = fields.Many2one(
        "workflow.instance",
        required=True,
        ondelete="cascade",
        index=True,
    )
    node_runtime_id = fields.Many2one(
        "workflow.node.runtime",
        index=True,
    )
    parent_token_id = fields.Many2one(
        "workflow.token",
        string="Parent Token",
        index=True,
    )
    state = fields.Selection(
        [
            ("active", "Active"),
            ("consumed", "Consumed"),
            ("cancelled", "Cancelled"),
        ],
        default="active",
        required=True,
        index=True,
    )
    cancel_reason = fields.Selection(
        [
            ("branch_superseded", "Branch Superseded"),
            ("instance_cancelled", "Instance Cancelled"),
            ("rework", "Rework Loop"),
        ],
    )
    created_at_utc = fields.Datetime(
        default=fields.Datetime.now,
        readonly=True,
    )
    consumed_at_utc = fields.Datetime(readonly=True)
    company_id = fields.Many2one(
        related="instance_id.company_id",
        store=True,
        index=True,
    )
