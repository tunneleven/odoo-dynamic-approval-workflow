from odoo.exceptions import UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..exceptions import WorkflowRuntimeError


@tagged("post_install", "-at_install")
class TestWorkflowToken(TransactionCase):
    """Tests for TASK-P3-003 workflow token state machine and fork/join operations."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.definition = cls.env["workflow.definition"].create(
            {
                "name": "Token Test Workflow",
                "definition_key": "token_test_workflow",
            }
        )
        cls.definition_version = cls.env["workflow.definition.version"].create(
            {
                "definition_id": cls.definition.id,
                "bpmn_xml": "<definitions/>",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Token Test Resource"})
        cls.instance = cls.env["workflow.instance"].create(
            {
                "definition_id": cls.definition.id,
                "definition_version_id": cls.definition_version.id,
                "res_model": "res.partner",
                "res_id": cls.partner.id,
            }
        )
        # Second instance for cross-instance guard tests
        cls.other_instance = cls.env["workflow.instance"].create(
            {
                "definition_id": cls.definition.id,
                "definition_version_id": cls.definition_version.id,
                "res_model": "res.partner",
                "res_id": cls.partner.id,
            }
        )

    def _create_node_runtime(self, instance=None, **overrides):
        """Create a node runtime with overridable defaults."""
        values = {
            "instance_id": (instance or self.instance).id,
            "node_id": "Activity_1",
            "node_type": "user_task",
        }
        values.update(overrides)
        return self.env["workflow.node.runtime"].create(values)

    def _create_token(self, **overrides):
        """Create a token with overridable defaults."""
        values = {
            "instance_id": self.instance.id,
        }
        values.update(overrides)
        return self.env["workflow.token"].create(values)

    # ------------------------------------------------------------------
    # Field defaults and creation
    # ------------------------------------------------------------------

    def test_create_sets_default_state_active(self):
        """DFR-04-013: tokens default to active state."""
        token = self._create_token()
        self.assertEqual(token.state, "active")
        self.assertTrue(token.created_at_utc)
        self.assertFalse(token.consumed_at_utc)
        self.assertFalse(token.cancel_reason)

    def test_create_sets_company_from_instance(self):
        """DFR-04-013: company_id is related from instance."""
        token = self._create_token()
        self.assertEqual(token.company_id, self.instance.company_id)

    # ------------------------------------------------------------------
    # Unlink immutability
    # ------------------------------------------------------------------

    def test_unlink_raises_user_error(self):
        """NFR-002: tokens cannot be deleted — state transitions only."""
        token = self._create_token()
        with self.assertRaises(UserError, msg="Token deletion must be blocked."):
            token.unlink()

    # ------------------------------------------------------------------
    # State machine — valid transitions
    # ------------------------------------------------------------------

    def test_transition_active_to_consumed(self):
        """FR-021: active token can be consumed."""
        token = self._create_token()
        token.write({"state": "consumed"})
        self.assertEqual(token.state, "consumed")
        self.assertTrue(token.consumed_at_utc, "consumed_at_utc must be auto-set.")

    def test_transition_active_to_cancelled(self):
        """FR-025: active token can be cancelled with a reason."""
        token = self._create_token()
        token.write({"state": "cancelled", "cancel_reason": "rework"})
        self.assertEqual(token.state, "cancelled")
        self.assertFalse(token.consumed_at_utc)

    # ------------------------------------------------------------------
    # State machine — invalid transitions
    # ------------------------------------------------------------------

    def test_transition_consumed_to_active_blocked(self):
        """DFR-04-013: consumed tokens cannot revert to active."""
        token = self._create_token()
        token.write({"state": "consumed"})
        with self.assertRaises(ValidationError):
            token.write({"state": "active"})

    def test_transition_cancelled_to_active_blocked(self):
        """DFR-04-013: cancelled tokens cannot revert to active."""
        token = self._create_token()
        token.write({"state": "cancelled", "cancel_reason": "rework"})
        with self.assertRaises(ValidationError):
            token.write({"state": "active"})

    def test_transition_consumed_to_cancelled_blocked(self):
        """DFR-04-013: consumed tokens cannot be cancelled."""
        token = self._create_token()
        token.write({"state": "consumed"})
        with self.assertRaises(ValidationError):
            token.write({"state": "cancelled", "cancel_reason": "rework"})

    # ------------------------------------------------------------------
    # Identity immutability
    # ------------------------------------------------------------------

    def test_write_rejects_instance_id_mutation(self):
        """DFR-04-013: instance_id is immutable after creation."""
        token = self._create_token()
        with self.assertRaises(ValidationError):
            token.write({"instance_id": self.other_instance.id})

    def test_write_rejects_parent_token_id_mutation(self):
        """DFR-04-013: parent_token_id is immutable after creation."""
        token = self._create_token()
        other_token = self._create_token()
        with self.assertRaises(ValidationError):
            token.write({"parent_token_id": other_token.id})

    def test_write_rejects_branch_id_mutation(self):
        """DFR-04-013: branch_id is immutable after creation."""
        token = self._create_token()
        with self.assertRaises(ValidationError):
            token.write({"branch_id": "mutated-branch"})

    # ------------------------------------------------------------------
    # Managed timestamps
    # ------------------------------------------------------------------

    def test_write_rejects_manual_consumed_at_utc(self):
        """DFR-04-013: consumed_at_utc is managed by state transitions."""
        token = self._create_token()
        with self.assertRaises(ValidationError):
            token.write({"consumed_at_utc": "2026-03-10 00:00:00"})

    # ------------------------------------------------------------------
    # Constraint validators
    # ------------------------------------------------------------------

    def test_cancelled_token_requires_cancel_reason(self):
        """DFR-04-013: cancelled tokens must have a cancel_reason."""
        token = self._create_token()
        with self.assertRaises(ValidationError):
            token.write({"state": "cancelled"})

    def test_active_token_rejects_cancel_reason(self):
        """DFR-04-013: active tokens must not have a cancel_reason."""
        with self.assertRaises(ValidationError):
            self._create_token(cancel_reason="rework")

    # ------------------------------------------------------------------
    # _consume
    # ------------------------------------------------------------------

    def test_consume_marks_active_tokens_consumed(self):
        """SDS §6.6: _consume sets state to consumed with timestamp."""
        token = self._create_token()
        token._consume()
        self.assertEqual(token.state, "consumed")
        self.assertTrue(token.consumed_at_utc)

    def test_consume_rejects_non_active_tokens(self):
        """SDS §6.6: _consume raises on already-consumed tokens."""
        token = self._create_token()
        token._consume()
        with self.assertRaises(WorkflowRuntimeError):
            token._consume()

    # ------------------------------------------------------------------
    # _advance
    # ------------------------------------------------------------------

    def test_advance_creates_child_at_target_node(self):
        """FR-021: _advance consumes parent and creates child at target."""
        node_a = self._create_node_runtime(node_id="Node_A")
        node_b = self._create_node_runtime(node_id="Node_B")
        token = self._create_token(node_runtime_id=node_a.id)

        child = token._advance(node_b)

        self.assertEqual(token.state, "consumed")
        self.assertEqual(child.state, "active")
        self.assertEqual(child.node_runtime_id, node_b)
        self.assertEqual(child.parent_token_id, token)
        self.assertEqual(child.instance_id, self.instance)

    def test_advance_rejects_cross_instance_target(self):
        """DFR-04-013: _advance blocks cross-instance node runtimes."""
        node_a = self._create_node_runtime(node_id="Node_A")
        other_node = self._create_node_runtime(
            instance=self.other_instance, node_id="Node_Other"
        )
        token = self._create_token(node_runtime_id=node_a.id)

        with self.assertRaises(WorkflowRuntimeError):
            token._advance(other_node)

    # ------------------------------------------------------------------
    # _fork
    # ------------------------------------------------------------------

    def test_fork_creates_n_children_with_unique_branch_ids(self):
        """FR-022: _fork creates N children with unique branch IDs."""
        node_a = self._create_node_runtime(node_id="Node_A")
        node_b = self._create_node_runtime(node_id="Node_B")
        node_c = self._create_node_runtime(node_id="Node_C")
        token = self._create_token()

        children = token._fork(node_a | node_b | node_c)

        self.assertEqual(token.state, "consumed")
        self.assertEqual(len(children), 3)
        branch_ids = children.mapped("branch_id")
        self.assertEqual(len(set(branch_ids)), 3, "Each child must have a unique branch_id.")
        for child in children:
            self.assertEqual(child.parent_token_id, token)
            self.assertEqual(child.state, "active")

    def test_fork_rejects_empty_targets(self):
        """FR-022: _fork requires at least one target node runtime."""
        token = self._create_token()
        empty = self.env["workflow.node.runtime"]
        with self.assertRaises(WorkflowRuntimeError):
            token._fork(empty)

    def test_fork_rejects_cross_instance_targets(self):
        """DFR-04-013: _fork blocks cross-instance node runtimes."""
        other_node = self._create_node_runtime(
            instance=self.other_instance, node_id="Node_Other"
        )
        token = self._create_token()
        with self.assertRaises(WorkflowRuntimeError):
            token._fork(other_node)

    # ------------------------------------------------------------------
    # _join("all")
    # ------------------------------------------------------------------

    def test_join_all_waits_for_active_siblings(self):
        """FR-022: _join('all') returns False while siblings are active."""
        node_a = self._create_node_runtime(node_id="Node_A")
        node_b = self._create_node_runtime(node_id="Node_B")
        parent = self._create_token()
        children = parent._fork(node_a | node_b)
        child_a = children[0]

        self.assertFalse(child_a._join("all"), "Join should wait while sibling is active.")

    def test_join_all_completes_when_all_consumed(self):
        """FR-022: _join('all') returns True when all siblings consumed."""
        node_a = self._create_node_runtime(node_id="Node_A")
        node_b = self._create_node_runtime(node_id="Node_B")
        parent = self._create_token()
        children = parent._fork(node_a | node_b)
        child_a, child_b = children[0], children[1]

        child_a._consume()
        self.assertTrue(child_b._join("all"), "Join should complete when all siblings consumed.")

    def test_join_all_treats_cancelled_siblings_as_done(self):
        """FR-022: _join('all') does not livelock on cancelled siblings."""
        node_a = self._create_node_runtime(node_id="Node_A")
        node_b = self._create_node_runtime(node_id="Node_B")
        node_c = self._create_node_runtime(node_id="Node_C")
        parent = self._create_token()
        children = parent._fork(node_a | node_b | node_c)
        child_a, child_b, child_c = children[0], children[1], children[2]

        child_a._consume()
        child_b.write({"state": "cancelled", "cancel_reason": "branch_superseded"})
        self.assertTrue(
            child_c._join("all"),
            "Join should complete when remaining siblings are consumed or cancelled.",
        )

    # ------------------------------------------------------------------
    # _join("any")
    # ------------------------------------------------------------------

    def test_join_any_returns_true_immediately(self):
        """FR-022: _join('any') completes on first arrival."""
        node_a = self._create_node_runtime(node_id="Node_A")
        node_b = self._create_node_runtime(node_id="Node_B")
        parent = self._create_token()
        children = parent._fork(node_a | node_b)
        child_a, child_b = children[0], children[1]

        self.assertTrue(child_a._join("any"))
        child_b.invalidate_recordset()
        self.assertEqual(
            child_b.state, "cancelled",
            "Remaining siblings must be cancelled with branch_superseded.",
        )
        self.assertEqual(child_b.cancel_reason, "branch_superseded")

    # ------------------------------------------------------------------
    # _join("quorum")
    # ------------------------------------------------------------------

    def test_join_quorum_waits_until_threshold_met(self):
        """FR-022: _join('quorum') waits until threshold met."""
        node_a = self._create_node_runtime(node_id="Node_A")
        node_b = self._create_node_runtime(node_id="Node_B")
        node_c = self._create_node_runtime(node_id="Node_C")
        parent = self._create_token()
        children = parent._fork(node_a | node_b | node_c)
        child_a, child_b = children[0], children[1]

        # Only 1 arrived (self), threshold is 2
        self.assertFalse(child_a._join("quorum", quorum_threshold=2))

        # Now child_a consumed, child_b arriving → 2 arrived
        child_a._consume()
        self.assertTrue(child_b._join("quorum", quorum_threshold=2))

    def test_join_quorum_excludes_cancelled_from_default_threshold(self):
        """FR-022: _join('quorum') default threshold excludes cancelled siblings."""
        node_a = self._create_node_runtime(node_id="Node_A")
        node_b = self._create_node_runtime(node_id="Node_B")
        node_c = self._create_node_runtime(node_id="Node_C")
        parent = self._create_token()
        children = parent._fork(node_a | node_b | node_c)
        child_a, child_b, child_c = children[0], children[1], children[2]

        # Cancel child_c upstream
        child_c.write({"state": "cancelled", "cancel_reason": "branch_superseded"})

        # Now default threshold should be 2 (live branches only), not 3
        child_a._consume()
        self.assertTrue(
            child_b._join("quorum"),
            "Default quorum threshold should exclude cancelled siblings.",
        )

    # ------------------------------------------------------------------
    # _join edge cases
    # ------------------------------------------------------------------

    def test_join_root_token_always_satisfies(self):
        """SDS §6.6: root tokens (no parent) always satisfy join."""
        token = self._create_token()
        self.assertTrue(token._join("all"))

    def test_join_non_active_token_returns_false(self):
        """SDS §6.6: consumed tokens cannot satisfy join."""
        token = self._create_token()
        token._consume()
        self.assertFalse(token._join("all"))

    # ------------------------------------------------------------------
    # Same-state write (no-op for state)
    # ------------------------------------------------------------------

    def test_same_state_write_does_not_restamp(self):
        """DFR-04-013: same-state writes must not trigger new timestamps."""
        token = self._create_token()
        token.write({"state": "consumed"})
        consumed_at = token.consumed_at_utc
        token.write({"state": "consumed"})
        self.assertEqual(
            token.consumed_at_utc,
            consumed_at,
            "Same-state write must not re-stamp consumed_at_utc.",
        )
