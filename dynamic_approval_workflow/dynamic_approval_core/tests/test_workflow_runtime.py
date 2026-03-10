import json

from odoo import fields
from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from ..exceptions import WorkflowConfigurationError, WorkflowRuntimeError


@tagged("post_install", "-at_install")
class TestWorkflowRuntime(TransactionCase):
    """Tests for runtime orchestration.

    Covers: DFR-04-001..DFR-04-014
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_admin = cls.env.ref("dynamic_approval_core.group_workflow_admin")
        cls.group_approver = cls.env.ref("dynamic_approval_core.group_workflow_approver")
        cls.workflow_admin_user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Runtime Workflow Admin",
                    "login": "runtime_workflow_admin@example.com",
                    "email": "runtime_workflow_admin@example.com",
                    "group_ids": [(6, 0, [cls.group_admin.id])],
                    "company_id": cls.env.company.id,
                    "company_ids": [(6, 0, [cls.env.company.id])],
                }
            )
        )
        cls.requester_user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Runtime Requester",
                    "login": "runtime_requester@example.com",
                    "email": "runtime_requester@example.com",
                    "group_ids": [(6, 0, [cls.group_approver.id])],
                    "company_id": cls.env.company.id,
                    "company_ids": [(6, 0, [cls.env.company.id])],
                }
            )
        )
        cls.other_approver_user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Runtime Other Approver",
                    "login": "runtime_other_approver@example.com",
                    "email": "runtime_other_approver@example.com",
                    "group_ids": [(6, 0, [cls.group_approver.id])],
                    "company_id": cls.env.company.id,
                    "company_ids": [(6, 0, [cls.env.company.id])],
                }
            )
        )
        cls.definition = cls.env["workflow.definition"].create(
            {
                "name": "Runtime Workflow",
                "definition_key": "runtime_workflow",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Runtime Resource"})
        cls._version_index = 0

    def _create_published_version(self, compiled_data, condition_rules=None):
        """Create a published workflow version with a compiled runtime artifact."""
        type(self)._version_index += 1
        version_number = type(self)._version_index
        bpmn_xml = "<definitions id='runtime_%s'/>" % version_number
        bpmn_hash = self.env["workflow.definition.version"]._compute_bpmn_hash(bpmn_xml)
        nodes = compiled_data.get("nodes") or []
        gateway_count = len(
            [
                node
                for node in nodes
                if (node.get("type") or node.get("node_type")) in {"exclusive_gateway", "parallel_gateway"}
            ]
        )
        compiled = self.env["workflow.definition.compiled"].create(
            {
                "bpmn_hash": bpmn_hash,
                "compiled_data": json.dumps(compiled_data),
                "node_count": len(nodes),
                "gateway_count": gateway_count,
            }
        )
        version = self.env["workflow.definition.version"].create(
            {
                "definition_id": self.definition.id,
                "bpmn_xml": bpmn_xml,
                "effective_from_utc": fields.Datetime.now(),
                "compiled_id": compiled.id,
            }
        )
        for rule_vals in condition_rules or []:
            self.env["workflow.condition.rule"].create(
                {
                    "definition_version_id": version.id,
                    **rule_vals,
                }
            )
        version.action_publish()
        self.assertTrue(version.version, "Published versions should receive a version number.")
        self.assertEqual(version.compiled_id, compiled, "Published version should keep the compiled runtime artifact.")
        self.assertEqual(version.bpmn_hash, bpmn_hash, "Published version should store the compiled BPMN hash.")
        return version

    def _create_instance(self, version, requester=None):
        """Create a workflow instance bound to the shared partner record."""
        requester = requester or self.env.user
        return self.env["workflow.instance"].create(
            {
                "definition_id": self.definition.id,
                "definition_version_id": version.id,
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "requester_id": requester.id,
            }
        )

    def test_compute_name_uses_definition_and_target_reference(self):
        """FR-021: instance name should include the definition and target reference."""
        version = self._create_published_version({"nodes": []})

        instance = self._create_instance(version)

        self.assertEqual(
            instance.name,
            "Runtime Workflow / res.partner,%s" % self.partner.id,
            "Workflow instance name must use the OMB target reference format.",
        )

    def test_action_start_requires_published_version_with_compiled_artifact(self):
        """FR-021: start should fail when the pinned version is not startable."""
        draft_version = self.env["workflow.definition.version"].create(
            {
                "definition_id": self.definition.id,
                "bpmn_xml": "<definitions/>",
            }
        )
        instance = self._create_instance(draft_version)

        with self.assertRaises(WorkflowConfigurationError):
            instance.action_start({"channel": "orm"})

    def test_action_start_advances_to_waiting_human_and_creates_task(self):
        """FR-021: start should activate the first human step and create a task."""
        version = self._create_published_version(
            {
                "start_node_id": "StartEvent_1",
                "nodes": [
                    {
                        "id": "StartEvent_1",
                        "type": "start_event",
                        "outgoing": ["UserTask_1"],
                    },
                    {
                        "id": "UserTask_1",
                        "type": "user_task",
                        "name": "Manager Approval",
                    },
                ],
            }
        )
        instance = self._create_instance(version)

        instance.action_start({"channel": "orm"})

        active_token = self.env["workflow.token"].search(
            [("instance_id", "=", instance.id), ("state", "=", "active")],
            limit=1,
        )
        task = self.env["workflow.task"].search(
            [("instance_id", "=", instance.id)],
            limit=1,
        )

        self.assertEqual(instance.state, "waiting_human", "Human wait nodes must drive the waiting_human state.")
        self.assertTrue(active_token, "Runtime start must create an active token for the current node.")
        self.assertEqual(
            active_token.node_runtime_id.node_id,
            "UserTask_1",
            "Runtime start must advance the active token to the first user task.",
        )
        self.assertTrue(task, "User-task activation must create a workflow task record.")
        self.assertEqual(task.name, "Manager Approval", "Created workflow tasks should use the compiled node label.")
        self.assertEqual(
            self.env["workflow.audit.event"].search_count(
                [
                    ("event_type", "=", "workflow.instance.started"),
                    ("object_ref", "=", "workflow.instance,%s" % instance.id),
                ]
            ),
            1,
            "Runtime start must emit the documented workflow.instance.started event.",
        )

    def test_action_start_routes_exclusive_gateway_with_condition_rule(self):
        """FR-023: exclusive gateways should evaluate condition rules deterministically."""
        version = self._create_published_version(
            {
                "start_node_id": "StartEvent_1",
                "nodes": [
                    {
                        "id": "StartEvent_1",
                        "type": "start_event",
                        "outgoing": ["Gateway_1"],
                    },
                    {
                        "id": "Gateway_1",
                        "type": "exclusive_gateway",
                        "outgoing": [
                            {
                                "target_node_id": "EndEvent_Approved",
                                "sequence": 10,
                                "condition": {
                                    "condition_type": "domain",
                                    "domain_filter": json.dumps([["id", "=", self.partner.id]]),
                                },
                            },
                            {"target_node_id": "EndEvent_Rejected", "sequence": 20, "is_default": True},
                        ],
                    },
                    {
                        "id": "EndEvent_Approved",
                        "type": "end_event",
                        "final_state": "completed_approved",
                    },
                    {
                        "id": "EndEvent_Rejected",
                        "type": "end_event",
                        "final_state": "completed_rejected",
                    },
                ],
            },
        )
        instance = self._create_instance(version)

        instance.action_start({"channel": "orm"})

        self.assertEqual(
            instance.state,
            "completed_approved",
            "Matching condition rules must route the instance to the approved end event.",
        )
        self.assertFalse(
            self.env["workflow.token"].search_count([("instance_id", "=", instance.id), ("state", "=", "active")]),
            "Terminal routing should leave no active tokens behind.",
        )
        self.assertEqual(
            self.env["workflow.audit.event"].search_count(
                [
                    ("event_type", "=", "workflow.instance.completed"),
                    ("object_ref", "=", "workflow.instance,%s" % instance.id),
                ]
            ),
            1,
            "Terminal routing must emit the workflow.instance.completed event.",
        )

    def test_action_start_parallel_gateway_forks_tokens_and_creates_tasks(self):
        """FR-022: runtime start should fork one token per parallel branch."""
        version = self._create_published_version(
            {
                "start_node_id": "StartEvent_1",
                "nodes": [
                    {
                        "id": "StartEvent_1",
                        "type": "start_event",
                        "outgoing": ["Gateway_1"],
                    },
                    {
                        "id": "Gateway_1",
                        "type": "parallel_gateway",
                        "outgoing": ["UserTask_A", "UserTask_B"],
                    },
                    {
                        "id": "UserTask_A",
                        "type": "user_task",
                        "name": "Parallel Approval A",
                    },
                    {
                        "id": "UserTask_B",
                        "type": "user_task",
                        "name": "Parallel Approval B",
                    },
                ],
            }
        )
        instance = self._create_instance(version)

        instance.action_start({"channel": "orm"})

        active_tokens = self.env["workflow.token"].search(
            [("instance_id", "=", instance.id), ("state", "=", "active")],
            order="id",
        )
        open_tasks = self.env["workflow.task"].search(
            [("instance_id", "=", instance.id), ("status", "not in", ("completed", "cancelled"))],
            order="id",
        )

        self.assertEqual(
            instance.state, "waiting_human", "Parallel human branches should leave the instance waiting on humans."
        )
        self.assertEqual(len(active_tokens), 2, "Parallel split should leave one active token per branch.")
        self.assertEqual(
            sorted(active_tokens.mapped("node_runtime_id.node_id")),
            ["UserTask_A", "UserTask_B"],
            "Forked runtime tokens should advance to each configured branch node.",
        )
        self.assertEqual(
            len(set(active_tokens.mapped("branch_id"))),
            1,
            "Forked branch tokens should share a branch group identifier for future joins.",
        )
        self.assertEqual(len(open_tasks), 2, "Each active human branch should create its own workflow task.")
        self.assertEqual(
            sorted(open_tasks.mapped("name")),
            ["Parallel Approval A", "Parallel Approval B"],
            "Parallel branch tasks should use the compiled node labels.",
        )

    def test_action_cancel_cancels_open_runtime_records(self):
        """FR-028: cancel should close tokens, tasks, and node runtimes consistently."""
        version = self._create_published_version(
            {
                "start_node_id": "StartEvent_1",
                "nodes": [
                    {
                        "id": "StartEvent_1",
                        "type": "start_event",
                        "outgoing": ["UserTask_1"],
                    },
                    {
                        "id": "UserTask_1",
                        "type": "user_task",
                        "name": "Cancelable Approval",
                    },
                ],
            }
        )
        instance = self._create_instance(version)
        instance.action_start({"channel": "orm"})

        instance.action_cancel("user_withdrew_request")

        self.assertEqual(instance.state, "cancelled", "Cancellation must move the instance into the cancelled state.")
        self.assertTrue(instance.ended_at_utc, "Cancellation must stamp the terminal end timestamp.")
        self.assertFalse(
            self.env["workflow.token"].search_count([("instance_id", "=", instance.id), ("state", "=", "active")]),
            "Cancellation must close every active runtime token.",
        )
        self.assertFalse(
            self.env["workflow.task"].search_count(
                [
                    ("instance_id", "=", instance.id),
                    ("status", "not in", ("completed", "cancelled")),
                ]
            ),
            "Cancellation must close every open workflow task.",
        )
        self.assertEqual(
            self.env["workflow.audit.event"].search_count(
                [
                    ("event_type", "=", "workflow.instance.cancelled"),
                    ("object_ref", "=", "workflow.instance,%s" % instance.id),
                ]
            ),
            1,
            "Cancellation must emit the workflow.instance.cancelled event.",
        )

    def test_runtime_actions_use_internal_elevation_for_requester_user(self):
        """FR-021/FR-028: authorized requester users should mutate runtime via internal elevation."""
        version = self._create_published_version(
            {
                "start_node_id": "StartEvent_1",
                "nodes": [
                    {
                        "id": "StartEvent_1",
                        "type": "start_event",
                        "outgoing": ["UserTask_1"],
                    },
                    {
                        "id": "UserTask_1",
                        "type": "user_task",
                        "name": "Approver Driven Task",
                    },
                ],
            }
        )
        instance = self._create_instance(version, requester=self.requester_user)

        instance.with_user(self.requester_user).action_start({"channel": "orm"})
        self.assertEqual(instance.state, "waiting_human", "Requester-triggered start should advance the runtime.")

        instance.with_user(self.requester_user).action_cancel("requester_cancelled")
        self.assertEqual(
            instance.state, "cancelled", "Requester-triggered cancel should succeed via internal runtime elevation."
        )

    def test_action_start_requires_requester_or_admin(self):
        """FR-021: non-requester actors must not start workflow instances."""
        version = self._create_published_version(
            {
                "start_node_id": "StartEvent_1",
                "nodes": [
                    {
                        "id": "StartEvent_1",
                        "type": "start_event",
                        "outgoing": ["UserTask_1"],
                    },
                    {
                        "id": "UserTask_1",
                        "type": "user_task",
                        "name": "Unauthorized Start",
                    },
                ],
            }
        )
        instance = self._create_instance(version, requester=self.requester_user)

        with self.assertRaises(AccessError):
            instance.with_user(self.other_approver_user).action_start({"channel": "orm"})

    def test_action_start_missing_condition_rule_incidents_instance(self):
        """FR-023: missing condition rules should fail closed instead of routing the instance."""
        version = self._create_published_version(
            {
                "start_node_id": "StartEvent_1",
                "nodes": [
                    {
                        "id": "StartEvent_1",
                        "type": "start_event",
                        "outgoing": ["Gateway_1"],
                    },
                    {
                        "id": "Gateway_1",
                        "type": "exclusive_gateway",
                        "outgoing": [
                            {
                                "target_node_id": "EndEvent_Approved",
                                "sequence": 10,
                                "condition_rule_id": 999999,
                            },
                            {"target_node_id": "EndEvent_Rejected", "sequence": 20, "is_default": True},
                        ],
                    },
                    {
                        "id": "EndEvent_Approved",
                        "type": "end_event",
                        "final_state": "completed_approved",
                    },
                    {
                        "id": "EndEvent_Rejected",
                        "type": "end_event",
                        "final_state": "completed_rejected",
                    },
                ],
            }
        )
        instance = self._create_instance(version)

        instance.action_start({"channel": "orm"})

        incident = self.env["workflow.incident"].search(
            [("instance_id", "=", instance.id), ("reason_code", "=", "runtime_configuration_error")],
            limit=1,
        )
        self.assertEqual(instance.state, "error_incident", "Missing condition rules must incident the runtime.")
        self.assertTrue(incident, "Missing condition rules must record a runtime configuration incident.")

    def test_action_recover_requires_resolved_incidents(self):
        """FR-028: recover should block until the incident queue is resolved."""
        version = self._create_published_version({"nodes": []})
        instance = self._create_instance(version)
        instance.write({"state": "error_incident"})
        incident = self.env["workflow.incident"].create(
            {
                "instance_id": instance.id,
                "category": "integrity_failure",
                "severity": "high",
                "reason_code": "runtime_tick_failed",
                "description": "Runtime failed during testing.",
                "company_id": self.env.company.id,
            }
        )

        with self.assertRaises(WorkflowRuntimeError):
            instance.with_user(self.workflow_admin_user).action_recover()

        incident.action_triage()
        incident.action_resolve()
        instance.with_user(self.workflow_admin_user).action_recover()

        self.assertEqual(instance.state, "running", "Recovered instances should re-enter the running state.")

    def test_action_recover_requires_admin_actor(self):
        """FR-068: recover should remain restricted to workflow admins."""
        version = self._create_published_version({"nodes": []})
        instance = self._create_instance(version, requester=self.requester_user)
        instance.write({"state": "error_incident"})
        incident = self.env["workflow.incident"].create(
            {
                "instance_id": instance.id,
                "category": "integrity_failure",
                "severity": "high",
                "reason_code": "runtime_tick_failed",
                "description": "Recover authorization test.",
                "company_id": self.env.company.id,
            }
        )
        incident.action_triage()
        incident.action_resolve()

        with self.assertRaises(AccessError):
            instance.with_user(self.requester_user).action_recover()

    def test_action_cancel_requires_admin_for_incidented_instances(self):
        """FR-068: incidented-instance cancellation should remain admin-only."""
        version = self._create_published_version({"nodes": []})
        instance = self._create_instance(version, requester=self.requester_user)
        instance.write({"state": "error_incident"})

        with self.assertRaises(AccessError):
            instance.with_user(self.requester_user).action_cancel("requester_cancelled_incident")

        instance.with_user(self.workflow_admin_user).action_cancel("admin_cancelled_incident")
        self.assertEqual(instance.state, "cancelled", "Workflow admins should be able to cancel incidented instances.")
