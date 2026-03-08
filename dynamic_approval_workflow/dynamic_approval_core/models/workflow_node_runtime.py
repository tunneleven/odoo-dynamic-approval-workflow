from odoo import api, fields, models


class WorkflowNodeRuntime(models.Model):
    """Runtime status for a single BPMN node within an instance.

    SRS: FR-021..FR-025  |  DFR: DFR-04-014
    """

    _name = "workflow.node.runtime"
    _description = "Workflow Node Runtime"
    _order = "instance_id, sequence"

    instance_id = fields.Many2one(
        "workflow.instance",
        required=True,
        ondelete="cascade",
        index=True,
    )
    node_id = fields.Char(
        string="BPMN Node ID",
        required=True,
        index=True,
    )
    node_type = fields.Selection(
        [
            ("start_event", "Start Event"),
            ("end_event", "End Event"),
            ("user_task", "User Task"),
            ("exclusive_gateway", "Exclusive Gateway"),
            ("parallel_gateway", "Parallel Gateway"),
            ("timer_event", "Timer Event"),
        ],
        required=True,
    )
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("active", "Active"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
            ("error", "Error"),
        ],
        default="pending",
        required=True,
        index=True,
    )
    sequence = fields.Integer(default=10)
    activated_at_utc = fields.Datetime()
    completed_at_utc = fields.Datetime()
    company_id = fields.Many2one(
        related="instance_id.company_id",
        store=True,
        index=True,
    )

    @api.model
    def _cron_discover_expired_timers(self):
        """Discover timer nodes ready for asynchronous execution.

        The current runtime schema does not yet persist timer deadlines on
        node runtimes, so this scheduler entrypoint remains a safe no-op
        until later runtime tasks add deadline metadata.
        """

        return 0
