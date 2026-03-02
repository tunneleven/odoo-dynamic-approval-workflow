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
        cls.other_company = cls.env["res.company"].create({"name": "Other Company"})
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

    def test_definition_key_regex_validation(self):
        valid_keys = ["abc", "a12", "a_b", "a" + ("z" * 63)]
        invalid_keys = ["ab", "A_bc", "1abc", "a-b", "a" + ("z" * 64)]

        for key in valid_keys:
            definition = self.env["workflow.definition"].create(
                {
                    "name": f"Valid {key}",
                    "definition_key": key,
                    "company_id": self.other_company.id,
                }
            )
            self.assertEqual(definition.definition_key, key, "Valid key should be accepted")

        for key in invalid_keys:
            with self.assertRaises(ValidationError):
                self.env["workflow.definition"].create(
                    {
                        "name": f"Invalid {key}",
                        "definition_key": key,
                        "company_id": self.other_company.id,
                    }
                )

    def test_unlink_blocked_when_published_version_exists(self):
        definition = self.env["workflow.definition"].create(
            {
                "name": "Protected Workflow",
                "definition_key": "protected_wf",
            }
        )
        version = self.env["workflow.definition.version"].create(
            {
                "definition_id": definition.id,
                "bpmn_xml": "<xml/>",
                "effective_from_utc": fields.Datetime.now(),
            }
        )
        version.action_publish()

        with self.assertRaises(ValidationError):
            definition.unlink()

    def test_unlink_allowed_without_published_versions(self):
        draft_definition = self.env["workflow.definition"].create(
            {
                "name": "Draft Workflow",
                "definition_key": "draft_wf",
            }
        )
        self.env["workflow.definition.version"].create(
            {
                "definition_id": draft_definition.id,
                "bpmn_xml": "<xml/>",
            }
        )
        draft_definition.unlink()
        self.assertFalse(
            self.env["workflow.definition"].search([("id", "=", draft_definition.id)]),
            "Definition with only draft versions should be deletable",
        )

        archived_definition = self.env["workflow.definition"].create(
            {
                "name": "Archived Workflow",
                "definition_key": "archived_wf",
            }
        )
        archived_version = self.env["workflow.definition.version"].create(
            {
                "definition_id": archived_definition.id,
                "bpmn_xml": "<xml/>",
                "effective_from_utc": fields.Datetime.now(),
            }
        )
        archived_version.action_publish()
        archived_version.action_archive()
        archived_definition.unlink()
        self.assertFalse(
            self.env["workflow.definition"].search([("id", "=", archived_definition.id)]),
            "Definition with only archived versions should be deletable",
        )

    def test_tag_company_default_and_uniqueness(self):
        tag = self.env["workflow.definition.tag"].create({"name": "Finance"})
        self.assertEqual(tag.company_id, self.env.company, "Tag company should default to env.company")
        self.assertEqual(tag.color, 0, "Tag color should default to 0")

        with self.assertRaises(Exception):
            self.env["workflow.definition.tag"].create(
                {
                    "name": "Finance",
                    "company_id": self.env.company.id,
                }
            )

        other_tag = self.env["workflow.definition.tag"].create(
            {
                "name": "Finance",
                "company_id": self.other_company.id,
            }
        )
        self.assertEqual(
            other_tag.company_id,
            self.other_company,
            "Same tag name should be allowed in a different company",
        )

    def test_definition_rejects_cross_company_tags(self):
        other_tag = self.env["workflow.definition.tag"].create(
            {
                "name": "Other Company Tag",
                "company_id": self.other_company.id,
            }
        )
        with self.assertRaises(ValidationError):
            self.definition.write({"tag_ids": [(6, 0, [other_tag.id])]})

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
