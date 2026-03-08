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

    def _assert_acl_contract(self, xmlid, model_name, group_xmlid, expected_perms):
        acl = self.env.ref(f"dynamic_approval_core.{xmlid}", raise_if_not_found=False)
        self.assertTrue(acl, f"Missing ACL row {xmlid}")
        self.assertEqual(acl.model_id.model, model_name, f"ACL {xmlid} must target {model_name}")
        self.assertEqual(
            acl.group_id,
            self.env.ref(f"dynamic_approval_core.{group_xmlid}"),
            f"ACL {xmlid} must target {group_xmlid}",
        )
        self.assertEqual(
            (acl.perm_read, acl.perm_write, acl.perm_create, acl.perm_unlink),
            expected_perms,
            f"ACL {xmlid} permissions do not match the security matrix",
        )

    def test_binding_and_scope_acl_rows_match_omb_contract(self):
        for xmlid, model_name, group_xmlid, expected_perms in (
            ("access_binding_approver", "workflow.binding", "group_workflow_approver", (True, False, False, False)),
            ("access_binding_designer", "workflow.binding", "group_workflow_designer", (True, True, True, False)),
            ("access_binding_admin", "workflow.binding", "group_workflow_admin", (True, True, True, True)),
            ("access_binding_auditor", "workflow.binding", "group_workflow_auditor", (True, False, False, False)),
            (
                "access_binding_scope_designer",
                "workflow.binding.scope",
                "group_workflow_designer",
                (True, True, True, True),
            ),
            (
                "access_binding_scope_admin",
                "workflow.binding.scope",
                "group_workflow_admin",
                (True, True, True, True),
            ),
            (
                "access_binding_scope_auditor",
                "workflow.binding.scope",
                "group_workflow_auditor",
                (True, False, False, False),
            ),
        ):
            self._assert_acl_contract(xmlid, model_name, group_xmlid, expected_perms)

        for legacy_xmlid in (
            "access_workflow_binding_approver",
            "access_workflow_binding_designer",
            "access_workflow_binding_admin",
            "access_workflow_binding_auditor",
            "access_workflow_binding_scope_designer",
            "access_workflow_binding_scope_admin",
        ):
            self.assertFalse(
                self.env.ref(f"dynamic_approval_core.{legacy_xmlid}", raise_if_not_found=False),
                f"Legacy ACL xmlid {legacy_xmlid} should not be present",
            )

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
