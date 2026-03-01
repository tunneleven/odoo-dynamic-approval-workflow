from odoo import fields, models


class WorkflowRetentionPolicy(models.Model):
    """Policy-driven retention profile for completed workflow data.

    Profiles: ``short_term`` (90 d), ``standard`` (365 d),
    ``compliance_extended`` (7 y).

    SDS: §14 Retention and Archival Design
    SRS: FR-076  |  DFR: DFR-09-005
    """

    _name = "workflow.retention.policy"
    _description = "Workflow Retention Policy"
    _order = "sequence"

    name = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    profile = fields.Selection(
        [
            ("short_term", "Short Term (90 days)"),
            ("standard", "Standard (365 days)"),
            ("compliance_extended", "Compliance Extended (7 years)"),
        ],
        required=True,
        default="standard",
    )
    retention_days = fields.Integer(
        required=True,
        default=365,
        help="Days after terminal state before archival eligibility.",
    )
    applies_to_definition_ids = fields.Many2many(
        "workflow.definition",
        string="Applies To Definitions",
        help="Leave empty to apply as default policy.",
    )
    legal_hold = fields.Boolean(
        default=False,
        help="When True, matching instances are exempt from archival/purge.",
    )
    is_active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
