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
        cls.group_workflow_admin = cls.env.ref("dynamic_approval_core.group_workflow_admin")
        cls.workflow_admin_user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Workflow Admin User",
                    "login": "workflow_admin_user@example.com",
                    "email": "workflow_admin_user@example.com",
                    "group_ids": [(6, 0, [cls.group_workflow_admin.id])],
                    "company_id": cls.env.company.id,
                    "company_ids": [(6, 0, [cls.env.company.id])],
                }
            )
        )
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

    def test_active_binding_create_auto_applies_interceptor_patch(self):
        binding = self._create_binding(
            target_action_method="action_triage",
            enforcement_mode="orm_enforced",
            is_active=True,
        )

        incident = self._create_incident()
        with patch.object(
            type(binding),
            "evaluate_gate",
            return_value={"state": "allowed", "reason_code": "allowed"},
        ) as evaluate_gate:
            incident.action_triage()

        self.assertEqual(evaluate_gate.call_count, 1, "Active binding create must activate interceptor.")
        self.assertEqual(incident.state, "triaged")

    def test_untrusted_bypass_token_does_not_skip_gate_evaluation(self):
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
        ) as evaluate_gate:
            with self.assertRaises(WorkflowGateBlockedError):
                incident.with_context(_workflow_bypass_token="user-supplied-token").action_triage()

        self.assertEqual(evaluate_gate.call_count, 1)
        self.assertEqual(incident.state, "open")

    def test_trusted_bypass_requires_internal_origin_and_superuser(self):
        binding = self._create_binding(
            target_action_method="action_triage",
            enforcement_mode="orm_enforced",
            is_active=True,
        )
        WorkflowEnforcementInterceptor._apply_patches(self.env)

        non_sudo_incident = self._create_incident().with_user(self.workflow_admin_user)
        with patch.object(
            type(binding),
            "evaluate_gate",
            return_value={
                "state": "blocked",
                "reason_code": "pending_approval",
                "policy_message": "Approval required before triage.",
            },
        ) as evaluate_gate:
            with self.assertRaises(WorkflowGateBlockedError):
                non_sudo_incident.with_context(
                    _workflow_bypass_token="interceptor_incident",
                    _workflow_internal_origin=WorkflowEnforcementInterceptor._INTERNAL_BYPASS_ORIGIN,
                ).action_triage()
        self.assertEqual(evaluate_gate.call_count, 1)
        self.assertEqual(non_sudo_incident.state, "open")

        sudo_incident = self._create_incident()
        with patch.object(
            type(binding),
            "evaluate_gate",
            side_effect=AssertionError("Trusted internal bypass should skip evaluate_gate."),
        ):
            sudo_incident.sudo().with_context(
                _workflow_bypass_token="interceptor_incident",
                _workflow_internal_origin=WorkflowEnforcementInterceptor._INTERNAL_BYPASS_ORIGIN,
            ).action_triage()
        self.assertEqual(sudo_incident.state, "triaged")

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

    def test_gate_blocked_error_is_not_masked_by_fail_closed_handler(self):
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
            side_effect=WorkflowGateBlockedError("Already blocked by policy."),
        ):
            with self.assertRaisesRegex(WorkflowGateBlockedError, "Already blocked by policy."):
                incident.action_triage()

        self.assertEqual(incident.state, "open")

    def test_fail_closed_survives_incident_recording_failure(self):
        binding = self._create_binding(
            target_action_method="action_triage",
            enforcement_mode="orm_enforced",
            is_active=True,
        )
        WorkflowEnforcementInterceptor._apply_patches(self.env)

        incident = self._create_incident()
        with patch.object(type(binding), "evaluate_gate", side_effect=RuntimeError("gate exploded")):
            with patch.object(
                WorkflowEnforcementInterceptor,
                "_record_incident",
                side_effect=RuntimeError("incident write failed"),
            ):
                with self.assertRaises(WorkflowGateBlockedError):
                    incident.action_triage()

        self.assertEqual(incident.state, "open")

    def test_trusted_bypass_logs_channel_from_context(self):
        binding = self._create_binding(
            target_action_method="action_triage",
            enforcement_mode="orm_enforced",
            is_active=True,
        )
        WorkflowEnforcementInterceptor._apply_patches(self.env)

        observed_channels = []

        def _capture_log_event(*args, **kwargs):
            observed_channels.append(kwargs.get("channel"))

        incident = self._create_incident()
        with patch.object(
            WorkflowEnforcementInterceptor,
            "_log_gate_event",
            side_effect=_capture_log_event,
        ):
            with patch.object(
                type(binding),
                "evaluate_gate",
                side_effect=AssertionError("Trusted internal bypass should skip evaluate_gate."),
            ):
                incident.sudo().with_context(
                    _workflow_bypass_token="interceptor_incident",
                    _workflow_internal_origin=WorkflowEnforcementInterceptor._INTERNAL_BYPASS_ORIGIN,
                    _workflow_channel="cron",
                ).action_triage()

        self.assertEqual(observed_channels, ["cron"])
        self.assertEqual(incident.state, "triaged")

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
