from odoo import http
from odoo.http import request


class WorkflowController(http.Controller):
    """HTTP endpoints for workflow gate evaluation and status.

    SRS: FR-081 — expose gate state to frontend hook.
    """

    @http.route(
        "/dynamic_approval/gate/evaluate",
        type="json",
        auth="user",
    )
    def evaluate_gate(self, model, res_id, action_method):
        """Return gate state for a bound action.

        Returns dict with ``state`` key:
        ``blocked``, ``allowed``, or ``allowed_with_warning``.
        """
        # Stub — full implementation in later phase
        return {"state": "allowed"}
