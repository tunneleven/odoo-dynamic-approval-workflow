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
