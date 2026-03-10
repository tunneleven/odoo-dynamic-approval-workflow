from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWorkflowNodeRuntime(TransactionCase):
    """Tests for TASK-P3-002 node runtime state handling."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.definition = cls.env["workflow.definition"].create(
            {
                "name": "Node Runtime Workflow",
                "definition_key": "node_runtime_workflow",
            }
        )
        cls.definition_version = cls.env["workflow.definition.version"].create(
            {
                "definition_id": cls.definition.id,
                "bpmn_xml": "<definitions/>",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Node Runtime Resource"})
        cls.instance = cls.env["workflow.instance"].create(
            {
                "definition_id": cls.definition.id,
                "definition_version_id": cls.definition_version.id,
                "res_model": "res.partner",
                "res_id": cls.partner.id,
            }
        )

    def _create_node_runtime(self, **overrides):
        """Create a node runtime with overridable defaults."""
        values = {
            "instance_id": self.instance.id,
            "node_id": "Activity_1",
            "node_type": "user_task",
        }
        values.update(overrides)
        return self.env["workflow.node.runtime"].create(values)

    def test_create_sets_omb_defaults(self):
        """DFR-04-014: node runtime records start in the documented default state."""
        node_runtime = self._create_node_runtime()

        self.assertEqual(node_runtime.state, "pending", "Node runtime should default to the pending state.")
        self.assertEqual(node_runtime.sequence, 10, "Node runtime should default to sequence 10.")
        self.assertEqual(node_runtime.loop_iteration, 1, "Node runtime should start at loop iteration 1.")
        self.assertEqual(
            node_runtime.company_id,
            self.instance.company_id,
            "Node runtime company should be related from the workflow instance.",
        )
        self.assertFalse(node_runtime.activated_at_utc, "Pending node runtime should not be activated yet.")
        self.assertFalse(node_runtime.completed_at_utc, "Pending node runtime should not be completed yet.")

    def test_create_rejects_non_pending_initial_state(self):
        """DFR-04-014: node runtime records must begin in the pending state."""
        with self.assertRaises(ValidationError, msg="Node runtime should reject non-pending initial states."):
            self._create_node_runtime(state="active")

    def test_write_allows_documented_state_transitions(self):
        """FR-021: node runtime should follow the documented transition path."""
        node_runtime = self._create_node_runtime()

        node_runtime.write({"state": "active"})
        self.assertEqual(node_runtime.state, "active", "Pending node runtime should activate when the token arrives.")
        self.assertTrue(node_runtime.activated_at_utc, "Activation should stamp the activation timestamp.")
        self.assertFalse(node_runtime.completed_at_utc, "Active node runtime should not be terminal yet.")

        node_runtime.write({"state": "completed"})
        self.assertEqual(node_runtime.state, "completed", "Active node runtime should complete on decision resolution.")
        self.assertTrue(node_runtime.completed_at_utc, "Completion should stamp the terminal timestamp.")

    def test_write_rejects_invalid_state_transition(self):
        """DFR-04-014: invalid node runtime transitions must be blocked."""
        node_runtime = self._create_node_runtime()

        with self.assertRaises(ValidationError, msg="Pending node runtime must not jump directly to completed."):
            node_runtime.write({"state": "completed"})

    def test_loop_iteration_uses_default_and_configured_cap(self):
        """DFR-04-005: loop iteration must honor the default and configured caps."""
        with self.assertRaises(ValidationError, msg="Default loop cap should reject values above 5."):
            self._create_node_runtime(loop_iteration=6)

        self.env["ir.config_parameter"].set_param("daw.rework_max_loops", "6")
        node_runtime = self._create_node_runtime(loop_iteration=6, node_id="Activity_6")
        self.assertEqual(node_runtime.loop_iteration, 6, "Configured loop cap should allow iteration 6.")

        with self.assertRaises(ValidationError, msg="Configured loop cap should reject values above 6."):
            self._create_node_runtime(loop_iteration=7, node_id="Activity_7")

    def test_loop_iteration_rejects_out_of_range_values(self):
        """DFR-04-005: loop iteration must stay within the documented numeric range."""
        with self.assertRaises(ValidationError, msg="Loop iteration should reject values below 1."):
            self._create_node_runtime(loop_iteration=0)

        with self.assertRaises(ValidationError, msg="Loop iteration should reject values above 99."):
            self.env["ir.config_parameter"].set_param("daw.rework_max_loops", "99")
            self._create_node_runtime(loop_iteration=100)

    def test_write_same_state_does_not_restamp_timestamps(self):
        """DFR-04-014: managed timestamps must remain stable on no-op state writes."""
        node_runtime = self._create_node_runtime()

        node_runtime.write({"state": "active"})
        activated_at = node_runtime.activated_at_utc
        node_runtime.write({"state": "active"})
        self.assertEqual(
            node_runtime.activated_at_utc,
            activated_at,
            "Same-state active writes must not restamp the activation timestamp.",
        )

        node_runtime.write({"state": "completed"})
        completed_at = node_runtime.completed_at_utc
        node_runtime.write({"state": "completed"})
        self.assertEqual(
            node_runtime.completed_at_utc,
            completed_at,
            "Same-state terminal writes must not restamp the completion timestamp.",
        )

    def test_write_rejects_manual_timestamp_mutation(self):
        """DFR-04-014: managed timestamps must not be caller-writable."""
        node_runtime = self._create_node_runtime()

        with self.assertRaises(ValidationError, msg="Managed timestamps should reject manual writes."):
            node_runtime.write({"activated_at_utc": "2026-03-10 00:00:00"})

    def test_cron_discover_expired_timers_is_safe_no_op_without_deadline_fields(self):
        """FR-021: timer discovery should remain idempotent until timer metadata exists."""
        self._create_node_runtime(node_id="Timer_1", node_type="timer_event")

        discovered = self.env["workflow.node.runtime"]._cron_discover_expired_timers()

        self.assertEqual(discovered, 0, "Timer discovery should be a safe no-op without deadline metadata.")
