from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWorkflowIncident(TransactionCase):
    """Regression tests for incident state-machine transitions."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.base_vals = {
            "category": "enforcement_failure",
            "severity": "high",
        }

    def _new_incident(self):
        return self.env["workflow.incident"].create(dict(self.base_vals))

    def test_resolve_requires_triage_or_retry_state(self):
        incident = self._new_incident()
        with self.assertRaises(ValidationError):
            incident.action_resolve()

    def test_close_requires_resolved_state(self):
        incident = self._new_incident()
        with self.assertRaises(ValidationError):
            incident.action_close_with_exception()

        incident.action_triage()
        with self.assertRaises(ValidationError):
            incident.action_close_with_exception()

    def test_retry_only_allowed_from_triaged(self):
        incident = self._new_incident()
        with self.assertRaises(ValidationError):
            incident.action_retry()

        incident.action_triage()
        incident.action_retry()
        self.assertEqual(
            incident.state,
            "retry_scheduled",
            "Incident should move to 'retry_scheduled' after retry action from triaged state.",
        )
        self.assertEqual(
            incident.resolution_action,
            "retry",
            "Resolution action should be 'retry' after retry action from triaged state.",
        )

    def test_happy_path_triage_resolve_close(self):
        incident = self._new_incident()
        incident.action_triage()
        incident.action_resolve()
        incident.action_close()
        self.assertEqual(
            incident.state,
            "closed_with_exception",
            "Incident should be in 'closed_with_exception' after close action on a resolved incident.",
        )
        self.assertEqual(
            incident.resolution_action,
            "close_with_exception",
            "Resolution action should be 'close_with_exception' after close action on a resolved incident.",
        )
