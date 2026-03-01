from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWorkflowEnforcement(TransactionCase):
    """Tests for ORM enforcement interceptor.

    Covers: DFR-02-002..DFR-02-011
    ADR: ADR-002
    """

    def test_placeholder(self):
        """Placeholder — interceptor tests added during implementation."""
        self.assertTrue(True)
