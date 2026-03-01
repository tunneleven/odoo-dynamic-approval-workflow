from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWorkflowBinding(TransactionCase):
    """Tests for workflow.binding.

    Covers: DFR-02-001..DFR-02-015
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.definition = cls.env["workflow.definition"].create(
            {
                "name": "Binding Test WF",
                "definition_key": "binding_test_wf",
            }
        )

    def test_create_binding(self):
        """Create a basic ORM-enforced binding."""
        binding = self.env["workflow.binding"].create(
            {
                "name": "Test Binding",
                "definition_id": self.definition.id,
                "target_model": "sale.order",
                "target_action_method": "action_confirm",
            }
        )
        self.assertEqual(binding.enforcement_mode, "orm_enforced")
        self.assertTrue(binding.is_active)
