from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRetention(TransactionCase):
    """Tests for workflow.retention.policy.

    Covers: DFR-09-005
    """

    def test_create_retention_policy(self):
        """Create a standard retention policy."""
        policy = self.env["workflow.retention.policy"].create(
            {
                "name": "Standard",
                "profile": "standard",
                "retention_days": 365,
            }
        )
        self.assertTrue(policy.id)
        self.assertTrue(policy.is_active)

    def test_legal_hold_default_false(self):
        """Legal hold defaults to False."""
        policy = self.env["workflow.retention.policy"].create(
            {
                "name": "Short",
                "profile": "short_term",
                "retention_days": 90,
            }
        )
        self.assertFalse(policy.legal_hold)
