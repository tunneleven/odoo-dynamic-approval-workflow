from datetime import timedelta
from unittest.mock import patch

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWorkflowCron(TransactionCase):
    """Tests for TASK-P2-008 scheduled actions and cron entrypoints."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.definition = cls.env["workflow.definition"].create(
            {
                "name": "Cron Workflow",
                "definition_key": "cron_workflow",
            }
        )
        cls.definition_version = cls.env["workflow.definition.version"].create(
            {
                "definition_id": cls.definition.id,
                "bpmn_xml": "<definitions/>",
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Cron Resource"})
        cls.instance = cls.env["workflow.instance"].create(
            {
                "definition_id": cls.definition.id,
                "definition_version_id": cls.definition_version.id,
                "res_model": "res.partner",
                "res_id": cls.partner.id,
            }
        )

    def _create_task(self, **overrides):
        """Create a workflow task with overridable defaults."""
        values = {
            "name": "Cron Task",
            "instance_id": self.instance.id,
            "status": "assigned",
        }
        values.update(overrides)
        return self.env["workflow.task"].create(values)

    def _create_access_grant(self, task, **overrides):
        """Create an access grant with overridable defaults."""
        values = {
            "task_id": task.id,
            "user_id": self.env.user.id,
            "res_model": "res.partner",
            "res_id": self.partner.id,
            "expires_at_utc": fields.Datetime.now() + timedelta(hours=1),
        }
        values.update(overrides)
        return self.env["workflow.access.grant"].create(values)

    def test_cron_records_match_omb_contract(self):
        """FR-073: cron data must match the OMB-04 schedule contract."""
        expected_records = {
            "dynamic_approval_core.ir_cron_timer_discovery": {
                "name": "Workflow: Discover Expired Timers",
                "model": "workflow.node.runtime",
                "code": "model._cron_discover_expired_timers()",
                "interval_number": 1,
                "interval_type": "minutes",
            },
            "dynamic_approval_core.ir_cron_sla_checker": {
                "name": "Workflow: Check SLA Deadlines",
                "model": "workflow.task",
                "code": "model._cron_check_sla()",
                "interval_number": 5,
                "interval_type": "minutes",
            },
            "dynamic_approval_core.ir_cron_deadline_checker": {
                "name": "Workflow: Check Task Deadlines",
                "model": "workflow.task",
                "code": "model._cron_check_deadlines()",
                "interval_number": 5,
                "interval_type": "minutes",
            },
            "dynamic_approval_core.ir_cron_grant_expiry": {
                "name": "Workflow: Expire Access Grants",
                "model": "workflow.access.grant",
                "code": "model._cron_expire_grants()",
                "interval_number": 5,
                "interval_type": "minutes",
            },
            "dynamic_approval_core.ir_cron_grant_reconciliation": {
                "name": "Workflow: Reconcile Orphan Grants",
                "model": "workflow.access.grant",
                "code": "model._cron_reconcile_orphan_grants()",
                "interval_number": 1,
                "interval_type": "hours",
            },
            "dynamic_approval_core.ir_cron_idempotency_purge": {
                "name": "Workflow: Purge Expired Idempotency Keys",
                "model": "workflow.idempotency.registry",
                "code": "model._cron_purge_expired()",
                "interval_number": 1,
                "interval_type": "days",
            },
        }

        for xmlid, expected in expected_records.items():
            cron = self.env.ref(xmlid)

            self.assertEqual(cron.name, expected["name"], f"{xmlid} must use the OMB-defined name.")
            self.assertEqual(
                cron.model_id.model,
                expected["model"],
                f"{xmlid} must target the documented model.",
            )
            self.assertEqual(cron.state, "code", f"{xmlid} must run in Python code mode.")
            self.assertEqual(cron.code, expected["code"], f"{xmlid} must call the documented method.")
            self.assertEqual(
                cron.interval_number,
                expected["interval_number"],
                f"{xmlid} must use the documented interval number.",
            )
            self.assertEqual(
                cron.interval_type,
                expected["interval_type"],
                f"{xmlid} must use the documented interval type.",
            )
            self.assertTrue(cron.active, f"{xmlid} must be active per OMB-04.")

    def test_cron_check_sla_marks_escalated_task_overdue(self):
        """DFR-05-011: SLA cron must refresh overdue markers for non-terminal tasks."""
        task = self._create_task(
            status="escalated",
            sla_due_at_utc=fields.Datetime.now() + timedelta(minutes=5),
        )
        future_now = fields.Datetime.now() + timedelta(hours=1)

        with patch("odoo.fields.Datetime.now", return_value=future_now):
            overdue_count = self.env["workflow.task"]._cron_check_sla()

        self.assertEqual(overdue_count, 1, "SLA cron should count the task that crossed its deadline.")
        self.assertTrue(task.is_overdue, "Escalated tasks past SLA must be marked overdue.")

    def test_cron_expire_grants_marks_due_grants_expired(self):
        """DFR-07-003: grant expiry cron must expire active grants past TTL."""
        task = self._create_task()
        expired_grant = self._create_access_grant(
            task,
            expires_at_utc=fields.Datetime.now() - timedelta(minutes=10),
        )
        active_grant = self._create_access_grant(task)

        expired_count = self.env["workflow.access.grant"]._cron_expire_grants()

        self.assertEqual(expired_count, 1, "Grant expiry cron should process only expired active grants.")
        self.assertEqual(expired_grant.state, "expired", "Expired grant must transition to expired.")
        self.assertEqual(
            expired_grant.revoke_reason,
            "ttl_expired",
            "Expired grant must record the TTL expiry reason.",
        )
        self.assertEqual(active_grant.state, "active", "Unexpired grant must remain active.")
        log_count = self.env["workflow.access.grant.log"].search_count(
            [("grant_id", "=", expired_grant.id), ("event_type", "=", "expired")]
        )
        self.assertEqual(log_count, 1, "Grant expiry cron must create one expiration log entry.")

    def test_cron_reconcile_orphan_grants_revokes_completed_task_grants(self):
        """SRS 7.3: reconciliation cron must revoke orphan grants."""
        task = self._create_task()
        reconciled_grant = self._create_access_grant(task)
        task.write({"status": "completed"})

        reconciled_count = self.env["workflow.access.grant"]._cron_reconcile_orphan_grants()

        self.assertEqual(
            reconciled_count,
            1,
            "Grant reconciliation cron should revoke active grants for completed tasks.",
        )
        self.assertEqual(reconciled_grant.state, "revoked", "Reconciled orphan grants must be revoked.")
        self.assertEqual(
            reconciled_grant.revoke_reason,
            "task_completed",
            "Completed-task reconciliation must use the task_completed revoke reason.",
        )
        log_count = self.env["workflow.access.grant.log"].search_count(
            [("grant_id", "=", reconciled_grant.id), ("event_type", "=", "reconciled")]
        )
        self.assertEqual(log_count, 1, "Grant reconciliation cron must create one reconciliation log entry.")

    def test_cron_purge_expired_removes_old_idempotency_entries(self):
        """SDS 10.5: purge cron must delete expired idempotency keys only."""
        expired_entry = self.env["workflow.idempotency.registry"].create(
            {
                "operation_type": "start",
                "operation_subject_ref": "workflow.instance,%s" % self.instance.id,
                "idempotency_key": "expired-key",
                "operation_scope_hash": "expired-scope-hash",
                "payload_hash": "expired-payload-hash",
                "result_status": "success",
                "expires_at_utc": fields.Datetime.now() - timedelta(days=1),
                "company_id": self.env.company.id,
            }
        )
        retained_entry = self.env["workflow.idempotency.registry"].create(
            {
                "operation_type": "start",
                "operation_subject_ref": "workflow.instance,%s" % self.instance.id,
                "idempotency_key": "retained-key",
                "operation_scope_hash": "retained-scope-hash",
                "payload_hash": "retained-payload-hash",
                "result_status": "success",
                "expires_at_utc": fields.Datetime.now() + timedelta(days=1),
                "company_id": self.env.company.id,
            }
        )

        purged_count = self.env["workflow.idempotency.registry"]._cron_purge_expired()

        self.assertEqual(purged_count, 1, "Purge cron should delete only expired idempotency entries.")
        self.assertEqual(
            self.env["workflow.idempotency.registry"].search_count([("id", "=", expired_entry.id)]),
            0,
            "Expired idempotency entry must be deleted by the purge cron.",
        )
        self.assertEqual(
            self.env["workflow.idempotency.registry"].search_count([("id", "=", retained_entry.id)]),
            1,
            "Unexpired idempotency entry must be retained by the purge cron.",
        )
