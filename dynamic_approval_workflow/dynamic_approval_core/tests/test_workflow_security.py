from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWorkflowSecurity(TransactionCase):
    """Tests for security groups and record rules.

    Covers: SDS §15, SDS §9
    """

    def test_groups_exist(self):
        """All four security groups must be present."""
        module = "dynamic_approval_core"
        for xmlid in (
            "group_workflow_approver",
            "group_workflow_designer",
            "group_workflow_admin",
            "group_workflow_auditor",
        ):
            group = self.env.ref(f"{module}.{xmlid}", raise_if_not_found=False)
            self.assertTrue(group, f"Group {xmlid} not found")

    def test_binding_scope_record_rule_exists_with_company_domain(self):
        rule = self.env.ref(
            "dynamic_approval_core.rule_workflow_binding_scope_company",
            raise_if_not_found=False,
        )
        self.assertTrue(rule, "Missing workflow.binding.scope multi-company rule")
        self.assertEqual(rule.model_id.model, "workflow.binding.scope")
        self.assertIn("company_ids", rule.domain_force)

    def test_incident_admin_acl_disallows_unlink(self):
        group_admin = self.env.ref("dynamic_approval_core.group_workflow_admin")
        acl = self.env["ir.model.access"].search(
            [
                ("model_id.model", "=", "workflow.incident"),
                ("group_id", "=", group_admin.id),
            ],
            limit=1,
        )
        self.assertTrue(acl, "Missing ACL row for workflow.incident + admin group")
        self.assertFalse(acl.perm_unlink, "Incident admin ACL must not grant delete permission")

    def test_audit_event_admin_acl_disallows_write(self):
        group_admin = self.env.ref("dynamic_approval_core.group_workflow_admin")
        acl = self.env["ir.model.access"].search(
            [
                ("model_id.model", "=", "workflow.audit.event"),
                ("group_id", "=", group_admin.id),
            ],
            limit=1,
        )
        self.assertTrue(acl, "Missing ACL row for workflow.audit.event + admin group")
        self.assertFalse(acl.perm_write, "Audit-event admin ACL must not grant write permission")
