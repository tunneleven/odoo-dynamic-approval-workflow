from psycopg2.errors import UniqueViolation

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
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
        cls.fixed_effective_from_utc = fields.Datetime.to_datetime("2026-01-01 00:00:00")
        cls.other_company = cls.env["res.company"].create({"name": "Other Company"})
        cls.group_designer = cls.env.ref("dynamic_approval_core.group_workflow_designer")
        cls.group_approver = cls.env.ref("dynamic_approval_core.group_workflow_approver")
        cls.designer_user = cls.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Designer User",
                "login": "designer_user@example.com",
                "email": "designer_user@example.com",
                "group_ids": [(6, 0, [cls.group_designer.id])],
                "company_id": cls.env.company.id,
                "company_ids": [(6, 0, [cls.env.company.id])],
            }
        )
        cls.other_designer_user = cls.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Other Designer User",
                "login": "designer_user_other@example.com",
                "email": "designer_user_other@example.com",
                "group_ids": [(6, 0, [cls.group_designer.id])],
                "company_id": cls.other_company.id,
                "company_ids": [(6, 0, [cls.other_company.id])],
            }
        )
        cls.approver_user = cls.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": "Approver User",
                "login": "approver_user@example.com",
                "email": "approver_user@example.com",
                "group_ids": [(6, 0, [cls.group_approver.id])],
                "company_id": cls.env.company.id,
                "company_ids": [(6, 0, [cls.env.company.id])],
            }
        )
        cls.definition = cls.env["workflow.definition"].create(
            {
                "name": "Test Workflow",
                "definition_key": "test_wf",
            }
        )

    def test_definition_crud_lifecycle_create_publish_archive(self):
        definition = self.env["workflow.definition"].create(
            {
                "name": "Lifecycle Workflow",
                "definition_key": "lifecycle_wf",
            }
        )
        self.assertTrue(definition.id, "Definition create step should persist record")

        version = self.env["workflow.definition.version"].create(
            {
                "definition_id": definition.id,
                "bpmn_xml": "<xml/>",
                "effective_from_utc": self.fixed_effective_from_utc,
            }
        )
        self.assertEqual(version.state, "draft", "New versions should start in draft state")

        version.action_publish()
        self.assertEqual(version.state, "published", "Publish should transition draft to published")

        version.action_archive()
        self.assertEqual(version.state, "archived", "Archive should transition published to archived")

    def test_version_auto_increment_per_definition(self):
        definition = self.env["workflow.definition"].create(
            {
                "name": "Increment Workflow",
                "definition_key": "increment_wf",
            }
        )
        version_1 = self.env["workflow.definition.version"].create(
            {
                "definition_id": definition.id,
                "bpmn_xml": "<xml/>",
                "effective_from_utc": self.fixed_effective_from_utc,
            }
        )
        version_1.action_publish()

        version_2 = self.env["workflow.definition.version"].create(
            {
                "definition_id": definition.id,
                "bpmn_xml": "<xml/>",
                "effective_from_utc": fields.Datetime.to_datetime("2026-02-01 00:00:00"),
            }
        )
        version_2.action_publish()

        self.assertEqual(version_1.version, 1, "First published version should be version 1")
        self.assertEqual(version_2.version, 2, "Second published version should auto-increment to version 2")

    def test_multi_company_isolation_record_rules(self):
        main_definition = self.env["workflow.definition"].create(
            {
                "name": "Main Company Workflow",
                "definition_key": "main_company_wf",
                "company_id": self.env.company.id,
            }
        )
        other_definition = self.env["workflow.definition"].create(
            {
                "name": "Other Company Workflow",
                "definition_key": "other_company_wf",
                "company_id": self.other_company.id,
            }
        )

        visible_for_main_designer = self.env["workflow.definition"].with_user(self.designer_user).search(
            [("id", "in", [main_definition.id, other_definition.id])]
        )
        self.assertIn(main_definition, visible_for_main_designer, "Main-company designer must see own company definitions")
        self.assertNotIn(
            other_definition,
            visible_for_main_designer,
            "Main-company designer must not see other-company definitions",
        )

        visible_for_other_designer = self.env["workflow.definition"].with_user(self.other_designer_user).search(
            [("id", "in", [main_definition.id, other_definition.id])]
        )
        self.assertIn(
            other_definition,
            visible_for_other_designer,
            "Other-company designer must see own company definitions",
        )
        self.assertNotIn(
            main_definition,
            visible_for_other_designer,
            "Other-company designer must not see main-company definitions",
        )

    def test_security_group_permissions_designer_can_create_approver_cannot(self):
        designer_definition = self.env["workflow.definition"].with_user(self.designer_user).create(
            {
                "name": "Designer Created Workflow",
                "definition_key": "designer_created_wf",
            }
        )
        self.assertTrue(designer_definition.id, "Designer user should be able to create workflow definitions")

        with self.assertRaises(AccessError):
            self.env["workflow.definition"].with_user(self.approver_user).create(
                {
                    "name": "Approver Created Workflow",
                    "definition_key": "approver_created_wf",
                }
            )

    def test_create_definition(self):
        """DFR-01-001: create via UI without code changes."""
        self.assertTrue(self.definition.id)
        self.assertEqual(self.definition.definition_key, "test_wf")

    def test_unique_key_per_company(self):
        """Definition key must be unique per company."""
        with self.assertRaises(UniqueViolation):
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

    def test_definition_key_locked_after_first_publish(self):
        definition = self.env["workflow.definition"].create(
            {
                "name": "Key Lock Workflow",
                "definition_key": "key_lock_wf",
            }
        )
        definition.write({"definition_key": "key_lock_wf_renamed"})

        version = self.env["workflow.definition.version"].create(
            {
                "definition_id": definition.id,
                "bpmn_xml": "<xml/>",
                "effective_from_utc": self.fixed_effective_from_utc,
            }
        )
        version.action_publish()

        with self.assertRaises(ValidationError):
            definition.write({"definition_key": "key_lock_wf_second_rename"})

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
                "effective_from_utc": self.fixed_effective_from_utc,
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
                "effective_from_utc": self.fixed_effective_from_utc,
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

        with self.assertRaises(UniqueViolation):
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
                "effective_from_utc": self.fixed_effective_from_utc,
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
                "effective_from_utc": self.fixed_effective_from_utc,
            }
        )
        with self.assertRaises(ValidationError):
            version.action_clone()

    def test_published_immutable_fields(self):
        version = self.env["workflow.definition.version"].create(
            {
                "definition_id": self.definition.id,
                "bpmn_xml": "<xml/>",
                "effective_from_utc": self.fixed_effective_from_utc,
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

    def test_draft_revision_increments_on_each_draft_write(self):
        version = self.env["workflow.definition.version"].create(
            {
                "definition_id": self.definition.id,
                "bpmn_xml": "<xml/>",
            }
        )
        self.assertEqual(version.draft_revision, 1)

        version.write({"bpmn_xml": "<xml>updated-1</xml>"})
        self.assertEqual(version.draft_revision, 2)

        version.write(
            {
                "effective_from_utc": self.fixed_effective_from_utc,
            }
        )
        self.assertEqual(version.draft_revision, 3)
