from types import SimpleNamespace
from unittest.mock import Mock

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..exceptions import WorkflowGateBlockedError
from ..models.workflow_approval_mixin import WorkflowApprovalMixin


class _FakeEnv(dict):
    def __init__(self, *args, company_id=1, user_id=1, context=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.company = SimpleNamespace(id=company_id)
        self.user = SimpleNamespace(id=user_id)
        self.context = context or {}


class _FakeRecord:
    def __init__(self, env, model_name="x_test.workflow_target", record_id=1):
        self.env = env
        self._name = model_name
        self.id = record_id

    def ensure_one(self):
        return None


@tagged("post_install", "-at_install")
class TestWorkflowApprovalMixin(TransactionCase):
    """Tests for the approval mixin contract."""

    def test_mixin_declares_expected_computed_fields(self):
        mixin_model = self.env["workflow.approval.mixin"]
        workflow_instance_ids = mixin_model._fields["workflow_instance_ids"]
        workflow_state = mixin_model._fields["workflow_state"]
        approval_state = mixin_model._fields["approval_state"]
        active_instance_id = mixin_model._fields["active_instance_id"]
        active_instance_state = mixin_model._fields["active_instance_state"]

        self.assertEqual(workflow_instance_ids.type, "one2many")
        self.assertEqual(workflow_instance_ids.comodel_name, "workflow.instance")
        self.assertEqual(
            workflow_instance_ids.compute,
            "_compute_workflow_instance_ids",
            "workflow_instance_ids must stay search-backed and computed.",
        )
        self.assertFalse(workflow_instance_ids.store)
        self.assertEqual(workflow_state.compute, "_compute_workflow_state")
        self.assertEqual(
            approval_state.compute,
            "_compute_workflow_state",
            "approval_state must mirror workflow_state for target models.",
        )
        self.assertEqual(active_instance_id.type, "many2one")
        self.assertEqual(active_instance_id.comodel_name, "workflow.instance")
        self.assertEqual(active_instance_id.compute, "_compute_active_instance")
        self.assertEqual(active_instance_state.compute, "_compute_active_instance")

    def test_derive_approval_state_maps_runtime_states(self):
        self.assertEqual(
            WorkflowApprovalMixin._derive_approval_state(
                [SimpleNamespace(state="running")]
            ),
            "pending",
        )
        self.assertEqual(
            WorkflowApprovalMixin._derive_approval_state(
                [SimpleNamespace(state="completed_approved")]
            ),
            "approved",
        )
        self.assertEqual(
            WorkflowApprovalMixin._derive_approval_state(
                [SimpleNamespace(state="completed_rejected")]
            ),
            "rejected",
        )
        self.assertEqual(
            WorkflowApprovalMixin._derive_approval_state(
                [SimpleNamespace(state="cancelled")]
            ),
            "none",
        )

    def test_get_active_workflow_instance_returns_latest_pending_instance(self):
        workflow_instance_model = Mock()
        workflow_instance_model.sudo.return_value = workflow_instance_model
        workflow_instance_model.search.return_value = "instance-42"

        record = _FakeRecord(
            _FakeEnv({"workflow.instance": workflow_instance_model}, company_id=7),
            record_id=42,
        )

        result = WorkflowApprovalMixin._get_active_workflow_instance(record)

        self.assertEqual(result, "instance-42")
        workflow_instance_model.search.assert_called_once_with(
            [
                ("res_model", "=", "x_test.workflow_target"),
                ("res_id", "=", 42),
                ("state", "in", ["running", "waiting_human", "waiting_timer"]),
            ],
            order="id desc",
            limit=1,
        )

    def test_check_approval_gate_returns_allowed_when_no_binding_exists(self):
        binding_model = Mock()
        binding_model.sudo.return_value = binding_model
        binding_model.search.return_value = False

        record = _FakeRecord(
            _FakeEnv({"workflow.binding": binding_model}, company_id=11, user_id=23)
        )

        result = WorkflowApprovalMixin._check_approval_gate(record, "action_submit")

        self.assertEqual(result["state"], "allowed")
        self.assertEqual(result["reason_code"], "no_active_binding")

    def test_check_approval_gate_raises_when_binding_blocks_action(self):
        binding_model = Mock()
        binding_model.sudo.return_value = binding_model
        binding = Mock()
        binding.id = 99
        binding.evaluate_gate.return_value = {
            "state": "blocked",
            "reason_code": "pending_approval",
            "policy_message": "Approval required before submit.",
        }
        binding_model.search.return_value = binding

        record = _FakeRecord(
            _FakeEnv({"workflow.binding": binding_model}, company_id=11, user_id=23)
        )

        with self.assertRaisesRegex(
            WorkflowGateBlockedError,
            "Approval required before submit.",
        ):
            WorkflowApprovalMixin._check_approval_gate(record, "action_submit")

        binding.evaluate_gate.assert_called_once_with(
            {
                "model": "x_test.workflow_target",
                "res_ids": [1],
                "action_method": "action_submit",
                "actor_user_id": 23,
                "company_id": 11,
                "channel": "orm",
                "request_id": False,
            }
        )
