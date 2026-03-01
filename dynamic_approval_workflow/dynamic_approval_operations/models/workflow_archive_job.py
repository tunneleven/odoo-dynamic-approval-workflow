from odoo import fields, models


class WorkflowArchiveJob(models.Model):
    """Tracks archival/purge job executions with immutable audit.

    SDS: §14 Retention and Archival Design
    SRS: FR-076  |  DFR: DFR-09-005
    """

    _name = "workflow.archive.job"
    _description = "Workflow Archive Job"
    _order = "executed_at_utc desc"

    name = fields.Char(
        compute="_compute_name",
        store=True,
    )
    job_type = fields.Selection(
        [
            ("archive", "Archive"),
            ("purge", "Purge"),
        ],
        required=True,
    )
    retention_policy_id = fields.Many2one(
        "workflow.retention.policy",
        index=True,
    )
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("running", "Running"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
        required=True,
    )
    instances_processed = fields.Integer(default=0)
    instances_skipped = fields.Integer(
        default=0,
        help="Skipped due to legal hold or other constraints.",
    )
    error_log = fields.Text()
    executed_at_utc = fields.Datetime(readonly=True)
    completed_at_utc = fields.Datetime(readonly=True)
    executed_by_id = fields.Many2one("res.users")
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )

    def _compute_name(self):
        for record in self:
            record.name = (
                f"{record.job_type or 'job'}-{record.id or 'new'}"
            )
