from odoo import fields, models


class WorkflowInstance(models.Model):
    """Runtime workflow execution for a single business record.

    States follow SDS §6.5 / SRS-04 §5.2 operational semantics:
    ``running``, ``waiting_human``, ``waiting_timer``,
    ``completed_approved``, ``completed_rejected``, ``cancelled``,
    ``error_incident``.

    SRS: FR-021..FR-028  |  DFR: DFR-04-001..DFR-04-014
    """

    _name = "workflow.instance"
    _description = "Workflow Instance"
    _inherit = ["mail.thread"]
    _order = "create_date desc"

    name = fields.Char(
        compute="_compute_name",
        store=True,
    )
    definition_id = fields.Many2one(
        "workflow.definition",
        required=True,
        index=True,
    )
    definition_version_id = fields.Many2one(
        "workflow.definition.version",
        required=True,
        index=True,
        help="Pinned at start time — never changes during execution.",
    )
    state = fields.Selection(
        [
            ("running", "Running"),
            ("waiting_human", "Waiting — Human"),
            ("waiting_timer", "Waiting — Timer"),
            ("completed_approved", "Approved"),
            ("completed_rejected", "Rejected"),
            ("cancelled", "Cancelled"),
            ("error_incident", "Error / Incident"),
        ],
        default="running",
        required=True,
        tracking=True,
        index=True,
    )
    res_model = fields.Char(
        string="Resource Model",
        required=True,
        index=True,
    )
    res_id = fields.Many2oneReference(
        string="Resource ID",
        model_field="res_model",
        required=True,
    )
    started_at_utc = fields.Datetime(
        string="Started At (UTC)",
        default=fields.Datetime.now,
        readonly=True,
    )
    ended_at_utc = fields.Datetime(
        string="Ended At (UTC)",
        readonly=True,
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    requester_id = fields.Many2one(
        "res.users",
        string="Requester",
        default=lambda self: self.env.user,
        index=True,
    )
    correlation_id = fields.Char(
        size=64,
        index=True,
        help="End-to-end trace identifier.",
    )
    active = fields.Boolean(default=True)

    def _compute_name(self):
        for record in self:
            record.name = f"{record.definition_id.name or ''} #{record.id or 'new'}"
