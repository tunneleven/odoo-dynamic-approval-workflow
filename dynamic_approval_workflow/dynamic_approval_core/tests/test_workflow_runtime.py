import json

from odoo import fields
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
        cls.definition = cls.env["workflow.definition"].create(
            {
                "name": "Runtime Workflow",
                "definition_key": "runtime_workflow",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Runtime Resource"})
        cls._version_index = 0

    def _create_published_version(self, compiled_data):
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
        return self.env["workflow.definition.version"].create(
            {
                "definition_id": self.definition.id,
                "version": version_number,
                "state": "published",
                "bpmn_xml": bpmn_xml,
                "bpmn_hash": bpmn_hash,
                "effective_from_utc": fields.Datetime.now(),
                "published_at_utc": fields.Datetime.now(),
                "published_by_id": self.env.user.id,
                "compiled_id": compiled.id,
            }
        )

    def _create_instance(self, version):
        """Create a workflow instance bound to the shared partner record."""
        return self.env["workflow.instance"].create(
            {
                "definition_id": self.definition.id,
                "definition_version_id": version.id,
                "res_model": "res.partner",
                "res_id": self.partner.id,
                "requester_id": self.env.user.id,
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
                            {"target_node_id": "EndEvent_Approved", "sequence": 10},
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
        self.env["workflow.condition.rule"].create(
            {
                "name": "Partner Match",
                "definition_version_id": version.id,
                "source_node_id": "Gateway_1",
                "target_node_id": "EndEvent_Approved",
                "condition_type": "domain",
                "domain_filter": json.dumps([["id", "=", self.partner.id]]),
            }
        )
        self.env["workflow.condition.rule"].create(
            {
                "name": "Default Rejection",
                "definition_version_id": version.id,
                "source_node_id": "Gateway_1",
                "target_node_id": "EndEvent_Rejected",
                "condition_type": "domain",
                "domain_filter": json.dumps([["id", "=", 0]]),
                "is_default": True,
            }
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
            instance.action_recover()

        incident.action_triage()
        incident.action_resolve()
        instance.action_recover()

        self.assertEqual(instance.state, "running", "Recovered instances should re-enter the running state.")
