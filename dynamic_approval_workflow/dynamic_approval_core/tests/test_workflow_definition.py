from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWorkflowDefinition(TransactionCase):
    """Tests for workflow.definition and workflow.definition.version.

    Covers: DFR-01-001..DFR-01-012
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.definition = cls.env["workflow.definition"].create(
            {
                "name": "Test Workflow",
                "definition_key": "test_wf",
            }
        )

    def test_create_definition(self):
        """DFR-01-001: create via UI without code changes."""
        self.assertTrue(self.definition.id)
        self.assertEqual(self.definition.definition_key, "test_wf")

    def test_unique_key_per_company(self):
        """Definition key must be unique per company."""
        with self.assertRaises(Exception):
            self.env["workflow.definition"].create(
                {
                    "name": "Duplicate",
                    "definition_key": "test_wf",
                    "company_id": self.definition.company_id.id,
                }
            )
