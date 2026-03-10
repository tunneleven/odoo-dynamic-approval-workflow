from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..exceptions import WorkflowError, WorkflowRuntimeError


@tagged("post_install", "-at_install")
class TestWorkflowToken(TransactionCase):
    """Tests for TASK-P3-003 token lifecycle behavior."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.definition = cls.env["workflow.definition"].create(
            {
                "name": "Token Workflow",
                "definition_key": "token_workflow",
            }
        )
        cls.definition_version = cls.env["workflow.definition.version"].create(
            {
                "definition_id": cls.definition.id,
                "bpmn_xml": "<definitions/>",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Token Resource"})

    def _create_instance(self):
        """Create an isolated workflow instance for one token test."""
        return self.env["workflow.instance"].create(
            {
                "definition_id": self.definition.id,
                "definition_version_id": self.definition_version.id,
                "res_model": "res.partner",
                "res_id": self.partner.id,
            }
        )

    def _create_node_runtime(self, instance, node_id, node_type, state="active"):
        """Create a runtime node in the requested state."""
        values = {
            "instance_id": instance.id,
            "node_id": node_id,
            "node_type": node_type,
            "sequence": instance._next_node_sequence(),
            "state": state,
        }
        if state == "active":
            values["activated_at_utc"] = fields.Datetime.now()
        elif state in {"completed", "timed_out"}:
            values.update(
                {
                    "activated_at_utc": fields.Datetime.now(),
                    "completed_at_utc": fields.Datetime.now(),
                }
            )
        elif state == "skipped":
            values["completed_at_utc"] = fields.Datetime.now()
        return self.env["workflow.node.runtime"].create(values)

    def _create_token(self, instance, node_runtime=None, parent_token=None, branch_id=None, state="active"):
        """Create a token with overridable lineage fields."""
        values = {
            "instance_id": instance.id,
            "node_runtime_id": node_runtime.id if node_runtime else False,
            "parent_token_id": parent_token.id if parent_token else False,
            "branch_id": branch_id,
            "state": state,
        }
        if state == "consumed":
            values["consumed_at_utc"] = fields.Datetime.now()
        if state == "cancelled":
            values["cancel_reason"] = "branch_superseded"
        return self.env["workflow.token"].create(values)

    def test_unlink_is_blocked_by_never_delete_policy(self):
        """FR-025: token history must remain append-only."""
        instance = self._create_instance()
        node_runtime = self._create_node_runtime(instance, "Start_1", "start_event")
        token = self._create_token(instance, node_runtime=node_runtime)

        with self.assertRaises(WorkflowError, msg="Token unlink must stay blocked by the never-delete policy."):
            token.unlink()

    def test_advance_parallel_gateway_forks_children_with_shared_branch_group(self):
        """FR-022: parallel split should create one child token per outgoing branch."""
        instance = self._create_instance()
        split_runtime = self._create_node_runtime(instance, "Gateway_Split", "parallel_gateway")
        token = self._create_token(instance, node_runtime=split_runtime)
        runtime_artifact = {
            "nodes": [
                {
                    "id": "Gateway_Split",
                    "type": "parallel_gateway",
                    "outgoing": ["Task_A", "Task_B"],
                },
                {"id": "Task_A", "type": "user_task"},
                {"id": "Task_B", "type": "user_task"},
            ]
        }

        token._advance(runtime_artifact)

        child_tokens = self.env["workflow.token"].search(
            [("parent_token_id", "=", token.id), ("state", "=", "active")],
            order="id",
        )
        self.assertEqual(token.state, "consumed", "Parallel split should consume the parent token before forking.")
        self.assertEqual(len(child_tokens), 2, "Parallel split should create one active child token per branch.")
        self.assertTrue(child_tokens[0].branch_id, "Forked child tokens should receive a branch group identifier.")
        self.assertEqual(
            len(set(child_tokens.mapped("branch_id"))),
            1,
            "All child tokens from the same split should share one branch group identifier.",
        )
        self.assertEqual(
            sorted(child_tokens.mapped("node_runtime_id.node_id")),
            ["Task_A", "Task_B"],
            "Forked child tokens should point at the expected downstream nodes.",
        )

    def test_parallel_split_tolerates_string_incoming_flow_identifier(self):
        """FR-022: BPMN-style incoming flow IDs should not be misread as join counts."""
        instance = self._create_instance()
        split_runtime = self._create_node_runtime(instance, "Gateway_StringIncoming", "parallel_gateway")
        token = self._create_token(instance, node_runtime=split_runtime)
        runtime_artifact = {
            "nodes": [
                {
                    "id": "Gateway_StringIncoming",
                    "type": "parallel_gateway",
                    "incoming": "Flow_1",
                    "outgoing": ["Task_A", "Task_B"],
                },
                {"id": "Task_A", "type": "user_task"},
                {"id": "Task_B", "type": "user_task"},
            ]
        }

        token._advance(runtime_artifact)

        self.assertEqual(
            self.env["workflow.token"].search_count([("parent_token_id", "=", token.id), ("state", "=", "active")]),
            2,
            "A single incoming flow ID should still be treated as a split and create both branch tokens.",
        )

    def test_advance_parallel_gateway_without_outgoing_paths_raises_error(self):
        """FR-022: misconfigured parallel splits must fail closed."""
        instance = self._create_instance()
        split_runtime = self._create_node_runtime(instance, "Gateway_Broken", "parallel_gateway")
        token = self._create_token(instance, node_runtime=split_runtime)
        runtime_artifact = {
            "nodes": [
                {
                    "id": "Gateway_Broken",
                    "type": "parallel_gateway",
                    "outgoing": [],
                }
            ]
        }

        with self.assertRaises(
            WorkflowRuntimeError,
            msg="Parallel gateways without reachable outgoing paths should raise instead of stalling silently.",
        ):
            token._advance(runtime_artifact)

    def test_join_quorum_consumes_arrivals_and_cancels_remaining_branch(self):
        """FR-022/FR-024: quorum join should merge when the threshold is reached."""
        instance = self._create_instance()
        split_parent = self._create_token(instance, state="consumed")
        branch_group_id = "branch-group-1"
        branch_root_a = self._create_token(
            instance, parent_token=split_parent, branch_id=branch_group_id, state="consumed"
        )
        branch_root_b = self._create_token(
            instance, parent_token=split_parent, branch_id=branch_group_id, state="consumed"
        )
        branch_root_c = self._create_token(
            instance, parent_token=split_parent, branch_id=branch_group_id, state="consumed"
        )

        join_runtime_a = self._create_node_runtime(instance, "Join_1", "parallel_gateway")
        join_runtime_b = self._create_node_runtime(instance, "Join_1", "parallel_gateway")
        task_runtime_c = self._create_node_runtime(instance, "Task_C", "user_task")
        join_token_a = self._create_token(
            instance,
            node_runtime=join_runtime_a,
            parent_token=branch_root_a,
            branch_id=branch_group_id,
        )
        join_token_b = self._create_token(
            instance,
            node_runtime=join_runtime_b,
            parent_token=branch_root_b,
            branch_id=branch_group_id,
        )
        remaining_branch_token = self._create_token(
            instance,
            node_runtime=task_runtime_c,
            parent_token=branch_root_c,
            branch_id=branch_group_id,
        )
        open_task = self.env["workflow.task"].create(
            {
                "name": "Branch C Approval",
                "instance_id": instance.id,
                "node_runtime_id": task_runtime_c.id,
            }
        )
        runtime_artifact = {
            "nodes": [
                {
                    "id": "Join_1",
                    "type": "parallel_gateway",
                    "join_mode": "quorum",
                    "quorum_count": 2,
                    "outgoing": ["End_1"],
                },
                {"id": "End_1", "type": "end_event", "final_state": "completed_approved"},
            ]
        }

        join_token_b._advance(runtime_artifact)

        downstream_token = self.env["workflow.token"].search(
            [("instance_id", "=", instance.id), ("state", "=", "active"), ("node_runtime_id.node_id", "=", "End_1")],
            limit=1,
        )
        self.assertEqual(join_token_a.state, "consumed", "Quorum join should consume already-arrived sibling tokens.")
        self.assertEqual(join_token_b.state, "consumed", "Quorum join should consume the token that closed the quorum.")
        self.assertEqual(
            join_runtime_a.state, "completed", "Arrived join runtimes should complete when quorum is reached."
        )
        self.assertEqual(
            join_runtime_b.state, "completed", "Closing join runtime should complete when quorum is reached."
        )
        self.assertEqual(
            remaining_branch_token.state,
            "cancelled",
            "Remaining active branch tokens should be cancelled once quorum closes the join.",
        )
        self.assertEqual(
            remaining_branch_token.cancel_reason,
            "branch_superseded",
            "Superseded branch tokens should record the documented cancellation reason.",
        )
        self.assertEqual(
            task_runtime_c.state,
            "skipped",
            "Superseded branch runtimes should be skipped when the join resolves early.",
        )
        self.assertEqual(open_task.status, "cancelled", "Open tasks on superseded branches should be cancelled.")
        self.assertTrue(
            downstream_token, "Quorum join should create exactly one downstream token when the threshold is met."
        )
        self.assertEqual(
            downstream_token.parent_token_id,
            split_parent,
            "Merged downstream tokens should reconnect to the pre-split parent lineage for nested joins.",
        )
        self.assertFalse(
            downstream_token.branch_id,
            "Merged downstream tokens should restore the parent branch group after the join completes.",
        )

    def test_join_quorum_cancels_nested_descendant_tokens(self):
        """FR-024: superseded branches must cancel nested descendant work too."""
        instance = self._create_instance()
        split_parent = self._create_token(instance, state="consumed")
        branch_group_id = "outer-branch-group"
        branch_root_a = self._create_token(
            instance, parent_token=split_parent, branch_id=branch_group_id, state="consumed"
        )
        branch_root_b = self._create_token(
            instance, parent_token=split_parent, branch_id=branch_group_id, state="consumed"
        )
        branch_root_c = self._create_token(
            instance, parent_token=split_parent, branch_id=branch_group_id, state="consumed"
        )

        join_runtime_a = self._create_node_runtime(instance, "Join_Outer", "parallel_gateway")
        join_runtime_b = self._create_node_runtime(instance, "Join_Outer", "parallel_gateway")
        nested_split_runtime = self._create_node_runtime(instance, "Gateway_Inner", "parallel_gateway")
        nested_task_runtime = self._create_node_runtime(instance, "Task_Inner", "user_task")
        self._create_token(
            instance,
            node_runtime=join_runtime_a,
            parent_token=branch_root_a,
            branch_id=branch_group_id,
        )
        join_token_b = self._create_token(
            instance,
            node_runtime=join_runtime_b,
            parent_token=branch_root_b,
            branch_id=branch_group_id,
        )
        nested_split_token = self._create_token(
            instance,
            node_runtime=nested_split_runtime,
            parent_token=branch_root_c,
            branch_id=branch_group_id,
        )
        nested_child_token = self._create_token(
            instance,
            node_runtime=nested_task_runtime,
            parent_token=nested_split_token,
            branch_id="inner-branch-group",
        )
        nested_task = self.env["workflow.task"].create(
            {
                "name": "Nested Branch Approval",
                "instance_id": instance.id,
                "node_runtime_id": nested_task_runtime.id,
            }
        )
        runtime_artifact = {
            "nodes": [
                {
                    "id": "Join_Outer",
                    "type": "parallel_gateway",
                    "join_mode": "quorum",
                    "quorum_count": 2,
                    "outgoing": ["End_Outer"],
                },
                {"id": "End_Outer", "type": "end_event", "final_state": "completed_approved"},
            ]
        }

        join_token_b._advance(runtime_artifact)

        self.assertEqual(
            nested_split_token.state,
            "cancelled",
            "Superseded outer branches should cancel their active split tokens.",
        )
        self.assertEqual(
            nested_child_token.state,
            "cancelled",
            "Superseded outer branches should also cancel active descendant tokens with new branch groups.",
        )
        self.assertEqual(
            nested_split_runtime.state,
            "skipped",
            "Nested split runtimes on superseded branches should be skipped.",
        )
        self.assertEqual(
            nested_task_runtime.state,
            "skipped",
            "Nested descendant runtimes on superseded branches should be skipped.",
        )
        self.assertEqual(
            nested_task.status,
            "cancelled",
            "Nested open tasks on superseded branches should be cancelled.",
        )
