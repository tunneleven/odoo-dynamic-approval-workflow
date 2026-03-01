from odoo import fields, models


class WorkflowDiagramAsset(models.Model):
    """BPMN diagram asset metadata.

    Tracks bpmn-js library version and bundle status.

    ADR: ADR-003
    """

    _name = "workflow.diagram.asset"
    _description = "Workflow Diagram Asset"

    name = fields.Char(required=True)
    version = fields.Char(
        help="bpmn-js library version.",
    )
    asset_path = fields.Char(
        help="Relative path to bpmn-js distribution bundle.",
    )
    is_loaded = fields.Boolean(
        default=False,
        help="Whether the asset has been loaded in the current session.",
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
