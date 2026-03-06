from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..exceptions import WorkflowGateBlockedError
from ..models.workflow_enforcement_interceptor import WorkflowEnforcementInterceptor


@tagged("post_install", "-at_install")
class TestWorkflowEnforcement(TransactionCase):
    """Tests for ORM enforcement interceptor.

    Covers: DFR-02-002..DFR-02-011
    ADR: ADR-002
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.definition = cls.env["workflow.definition"].create(
            {
                "name": "Interceptor Test Workflow",
                "definition_key": "interceptor_test_workflow",
            }
        )
        cls._base_incident_vals = {
            "category": "enforcement_failure",
            "severity": "high",
        }

    def setUp(self):
        super().setUp()
        WorkflowEnforcementInterceptor._remove_patches(self.env)
        self._binding_sequence = 0

    def tearDown(self):
        WorkflowEnforcementInterceptor._remove_patches(self.env)
        super().tearDown()

    def _new_binding_vals(self, **overrides):
        self._binding_sequence += 1
        values = {
            "name": f"Interceptor Binding {self._binding_sequence}",
            "definition_id": self.definition.id,
            "target_model": "workflow.incident",
            "target_action_method": f"action_interceptor_{self._binding_sequence}",
            "enforcement_mode": "orm_enforced",
            "is_active": True,
        }
        values.update(overrides)
        return values

    def _create_binding(self, **overrides):
        return self.env["workflow.binding"].create(self._new_binding_vals(**overrides))

    def _create_incident(self):
        return self.env["workflow.incident"].create(dict(self._base_incident_vals))

    def test_interceptor_contract_declares_non_registered_abstract_model(self):
        self.assertFalse(
            WorkflowEnforcementInterceptor._register,
            "Interceptor model must stay unregistered and tableless.",
        )

    def test_apply_patches_targets_only_active_enforced_bindings(self):
        self._create_binding(
            target_action_method="action_triage",
            enforcement_mode="orm_enforced",
            is_active=True,
        )
        self._create_binding(
            target_action_method="action_retry",
            enforcement_mode="hybrid",
            is_active=True,
        )
        self._create_binding(
            target_action_method="action_resolve",
            enforcement_mode="ui_only",
            is_active=True,
        )
        self._create_binding(
            target_action_method="action_close_with_exception",
            enforcement_mode="orm_enforced",
            is_active=False,
        )

        WorkflowEnforcementInterceptor._apply_patches(self.env)

        patched_keys = set(WorkflowEnforcementInterceptor._patched_methods)
        self.assertIn(("workflow.incident", "action_triage"), patched_keys)
        self.assertIn(("workflow.incident", "action_retry"), patched_keys)
        self.assertNotIn(("workflow.incident", "action_resolve"), patched_keys)
        self.assertNotIn(("workflow.incident", "action_close_with_exception"), patched_keys)

    def test_bypass_token_skips_gate_evaluation_and_allows_call(self):
        binding = self._create_binding(
            target_action_method="action_triage",
            enforcement_mode="orm_enforced",
            is_active=True,
        )
        WorkflowEnforcementInterceptor._apply_patches(self.env)

        incident = self._create_incident()
        with patch.object(
            type(binding),
            "evaluate_gate",
            side_effect=AssertionError("evaluate_gate must be skipped for bypass token"),
        ):
            incident.with_context(_workflow_bypass_token="internal-only-token").action_triage()

        self.assertEqual(incident.state, "triaged")

    def test_blocked_gate_raises_workflow_gate_blocked_error(self):
        binding = self._create_binding(
            target_action_method="action_triage",
            enforcement_mode="orm_enforced",
            is_active=True,
        )
        WorkflowEnforcementInterceptor._apply_patches(self.env)

        incident = self._create_incident()
        with patch.object(
            type(binding),
            "evaluate_gate",
            return_value={
                "state": "blocked",
                "reason_code": "pending_approval",
                "policy_message": "Approval required before triage.",
            },
        ):
            with self.assertRaises(WorkflowGateBlockedError):
                incident.action_triage()

        self.assertEqual(incident.state, "open")

    def test_gate_evaluation_exception_fails_closed(self):
        binding = self._create_binding(
            target_action_method="action_triage",
            enforcement_mode="hybrid",
            is_active=True,
        )
        WorkflowEnforcementInterceptor._apply_patches(self.env)

        incident = self._create_incident()
        with patch.object(type(binding), "evaluate_gate", side_effect=RuntimeError("gate exploded")):
            with self.assertRaises(WorkflowGateBlockedError):
                incident.action_triage()

        self.assertEqual(incident.state, "open")

    def test_interceptor_records_all_channel_contexts_and_sudo_calls(self):
        binding = self._create_binding(
            target_action_method="action_triage",
            enforcement_mode="orm_enforced",
            is_active=True,
        )
        WorkflowEnforcementInterceptor._apply_patches(self.env)

        observed_contexts = []
        channels = ["ui", "rpc", "import", "server_action", "cron"]

        def _fake_gate(record_context):
            observed_contexts.append(dict(record_context))
            return {"state": "allowed", "reason_code": "allowed"}

        with patch.object(type(binding), "evaluate_gate", side_effect=_fake_gate):
            for channel in channels:
                incident = self._create_incident()
                incident.with_context(_workflow_channel=channel).action_triage()
                self.assertEqual(incident.state, "triaged")

            sudo_incident = self._create_incident()
            sudo_incident.sudo().with_context(_workflow_channel="cron").action_triage()
            self.assertEqual(sudo_incident.state, "triaged")

        observed_channels = {ctx.get("channel") for ctx in observed_contexts}
        self.assertTrue(set(channels).issubset(observed_channels))
        self.assertEqual(
            len(observed_contexts),
            len(channels) + 1,
            "Each channel and sudo call must pass through interceptor evaluation.",
        )
