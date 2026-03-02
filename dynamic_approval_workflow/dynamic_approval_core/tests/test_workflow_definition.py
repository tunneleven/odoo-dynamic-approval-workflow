from odoo import fields
from odoo.exceptions import ValidationError
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

    def test_publish_sets_version_and_metadata(self):
        version = self.env["workflow.definition.version"].create(
            {
                "definition_id": self.definition.id,
                "bpmn_xml": "<xml/>",
                "effective_from_utc": fields.Datetime.now(),
            }
        )
        version.action_publish()
        self.assertEqual(version.state, "published")
        self.assertTrue(version.version)
        self.assertTrue(version.bpmn_hash)
        self.assertTrue(version.published_at_utc)
        self.assertEqual(version.published_by_id, self.env.user)

    def test_clone_requires_published_source(self):
        version = self.env["workflow.definition.version"].create(
            {
                "definition_id": self.definition.id,
                "bpmn_xml": "<xml/>",
                "effective_from_utc": fields.Datetime.now(),
            }
        )
        with self.assertRaises(ValidationError):
            version.action_clone()

    def test_published_immutable_fields(self):
        version = self.env["workflow.definition.version"].create(
            {
                "definition_id": self.definition.id,
                "bpmn_xml": "<xml/>",
                "effective_from_utc": fields.Datetime.now(),
            }
        )
        version.action_publish()
        with self.assertRaises(ValidationError):
            version.write({"bpmn_xml": "<xml>changed</xml>"})

    def test_direct_publish_state_write_blocked_by_constraints(self):
        version = self.env["workflow.definition.version"].create(
            {
                "definition_id": self.definition.id,
                "bpmn_xml": "<xml/>",
            }
        )
        with self.assertRaises(ValidationError):
            version.write({"state": "published"})
