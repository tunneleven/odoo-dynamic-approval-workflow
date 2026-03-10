import json

from odoo import fields
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWorkflowConditionFollowerRule(TransactionCase):
    """Tests for workflow.condition.rule and workflow.follower.rule."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_designer = cls.env.ref("dynamic_approval_core.group_workflow_designer")
        cls.designer_user = (
            cls.env["res.users"]
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Condition Designer",
                    "login": "condition_designer@example.com",
                    "email": "condition_designer@example.com",
                    "group_ids": [(6, 0, [cls.group_designer.id])],
                    "company_id": cls.env.company.id,
                    "company_ids": [(6, 0, [cls.env.company.id])],
                }
            )
        )
        cls.definition = cls.env["workflow.definition"].create(
            {
                "name": "Condition Workflow",
                "definition_key": "condition_workflow",
            }
        )
        cls.version = cls.env["workflow.definition.version"].create(
            {
                "definition_id": cls.definition.id,
                "bpmn_xml": "<xml/>",
            }
        )

    def test_condition_rule_requires_value_by_type(self):
        with self.assertRaises(ValidationError):
            self.env["workflow.condition.rule"].create(
                {
                    "name": "Invalid Domain",
                    "definition_version_id": self.version.id,
                    "source_node_id": "Gateway_A",
                    "target_node_id": "Task_A",
                    "condition_type": "domain",
                }
            )

        with self.assertRaises(ValidationError):
            self.env["workflow.condition.rule"].create(
                {
                    "name": "Invalid Python",
                    "definition_version_id": self.version.id,
                    "source_node_id": "Gateway_A",
                    "target_node_id": "Task_B",
                    "condition_type": "python",
                }
            )

        domain_rule = self.env["workflow.condition.rule"].create(
            {
                "name": "Valid Domain",
                "definition_version_id": self.version.id,
                "source_node_id": "Gateway_A",
                "target_node_id": "Task_C",
                "condition_type": "domain",
                "domain_filter": json.dumps([["name", "=", "Alpha"]]),
            }
        )
        self.assertTrue(domain_rule, "Domain rule should be created with valid domain_filter")

        python_rule = self.env["workflow.condition.rule"].create(
            {
                "name": "Valid Python",
                "definition_version_id": self.version.id,
                "source_node_id": "Gateway_A",
                "target_node_id": "Task_D",
                "condition_type": "python",
                "python_code": "record.name == 'Alpha'",
            }
        )
        self.assertTrue(python_rule, "Python rule should be created with valid python_code")

    def test_condition_rule_python_is_admin_only(self):
        with self.assertRaises(AccessError):
            self.env["workflow.condition.rule"].with_user(self.designer_user).create(
                {
                    "name": "Designer Python",
                    "definition_version_id": self.version.id,
                    "source_node_id": "Gateway_P",
                    "target_node_id": "Task_P",
                    "condition_type": "python",
                    "python_code": "True",
                }
            )

    def test_condition_rule_published_version_is_immutable(self):
        version = self.env["workflow.definition.version"].create(
            {
                "definition_id": self.definition.id,
                "bpmn_xml": "<xml/>",
                "effective_from_utc": fields.Datetime.now(),
            }
        )
        rule = self.env["workflow.condition.rule"].create(
            {
                "name": "Published Rule",
                "definition_version_id": version.id,
                "source_node_id": "Gateway_IMM",
                "target_node_id": "Task_IMM",
                "condition_type": "domain",
                "domain_filter": json.dumps([["name", "=", "X"]]),
            }
        )
        version.action_publish()

        with self.assertRaises(ValidationError):
            rule.write({"name": "Changed"})
        with self.assertRaises(ValidationError):
            self.env["workflow.condition.rule"].create(
                {
                    "name": "Late Rule",
                    "definition_version_id": version.id,
                    "source_node_id": "Gateway_IMM",
                    "target_node_id": "Task_OTHER",
                    "condition_type": "domain",
                    "domain_filter": json.dumps([["name", "=", "Y"]]),
                }
            )
        with self.assertRaises(ValidationError):
            rule.unlink()

    def test_condition_rule_domain_filter_must_be_json_list(self):
        with self.assertRaises(ValidationError):
            self.env["workflow.condition.rule"].create(
                {
                    "name": "Invalid JSON",
                    "definition_version_id": self.version.id,
                    "source_node_id": "Gateway_B",
                    "target_node_id": "Task_A",
                    "condition_type": "domain",
                    "domain_filter": "not-json",
                }
            )

        with self.assertRaises(ValidationError):
            self.env["workflow.condition.rule"].create(
                {
                    "name": "Invalid Domain Shape",
                    "definition_version_id": self.version.id,
                    "source_node_id": "Gateway_B",
                    "target_node_id": "Task_B",
                    "condition_type": "domain",
                    "domain_filter": json.dumps({"name": "Alpha"}),
                }
            )

    def test_condition_rule_evaluate_domain_and_python(self):
        partner_true = self.env["res.partner"].create({"name": "Condition Alpha"})
        partner_false = self.env["res.partner"].create({"name": "Condition Beta"})

        domain_rule = self.env["workflow.condition.rule"].create(
            {
                "name": "Domain Eval",
                "definition_version_id": self.version.id,
                "source_node_id": "Gateway_C",
                "target_node_id": "Task_A",
                "condition_type": "domain",
                "domain_filter": json.dumps([["name", "=", "Condition Alpha"]]),
            }
        )
        self.assertTrue(domain_rule.evaluate(partner_true, {}), "Domain rule should match Condition Alpha")
        self.assertFalse(domain_rule.evaluate(partner_false, {}), "Domain rule should reject Condition Beta")

        python_rule = self.env["workflow.condition.rule"].create(
            {
                "name": "Python Eval",
                "definition_version_id": self.version.id,
                "source_node_id": "Gateway_C",
                "target_node_id": "Task_B",
                "condition_type": "python",
                "python_code": "record.name.startswith('Condition A')",
            }
        )
        self.assertTrue(python_rule.evaluate(partner_true, {}), "Python rule should match Condition Alpha")
        self.assertFalse(python_rule.evaluate(partner_false, {}), "Python rule should reject Condition Beta")

    def test_condition_rule_cascades_on_version_delete(self):
        definition = self.env["workflow.definition"].create(
            {
                "name": "Cascade Definition",
                "definition_key": "cascade_condition",
            }
        )
        version = self.env["workflow.definition.version"].create(
            {
                "definition_id": definition.id,
                "bpmn_xml": "<xml/>",
            }
        )
        rule = self.env["workflow.condition.rule"].create(
            {
                "name": "Cascade Rule",
                "definition_version_id": version.id,
                "source_node_id": "Gateway_D",
                "target_node_id": "Task_A",
                "condition_type": "domain",
                "domain_filter": json.dumps([["name", "=", "X"]]),
            }
        )
        version.unlink()
        self.assertFalse(
            self.env["workflow.condition.rule"].search([("id", "=", rule.id)]),
            "Condition rule should be deleted when definition version is deleted",
        )

    def test_follower_rule_required_fields_and_defaults(self):
        with self.assertRaises(ValidationError):
            self.env["workflow.follower.rule"].create(
                {
                    "name": "Group Missing",
                    "definition_version_id": self.version.id,
                    "follower_type": "group",
                }
            )

        with self.assertRaises(ValidationError):
            self.env["workflow.follower.rule"].create(
                {
                    "name": "Field Missing",
                    "definition_version_id": self.version.id,
                    "follower_type": "field",
                }
            )

        requester_rule = self.env["workflow.follower.rule"].create(
            {
                "name": "Requester Rule",
                "definition_version_id": self.version.id,
                "follower_type": "requester",
            }
        )
        self.assertEqual(
            requester_rule.completion_policy,
            "retained",
            "Completion policy must default to retained",
        )

    def test_follower_rule_resolve_followers(self):
        actor_user = self.env.ref("base.user_admin")
        partner = self.env["res.partner"].create(
            {
                "name": "Owner Partner",
                "user_id": actor_user.id,
            }
        )
        group_user = self.env["res.groups"].create({"name": "Follower Rule Test Group"})
        group_user.write({"user_ids": [(4, actor_user.id)]})

        requester_rule = self.env["workflow.follower.rule"].create(
            {
                "name": "Requester",
                "definition_version_id": self.version.id,
                "follower_type": "requester",
            }
        )
        requester_followers = requester_rule._resolve_followers(
            requester=actor_user,
            approvers=self.env["res.users"],
            record=partner,
        )
        self.assertIn(actor_user, requester_followers, "Requester should be included for requester rule")

        group_rule = self.env["workflow.follower.rule"].create(
            {
                "name": "Group",
                "definition_version_id": self.version.id,
                "follower_type": "group",
                "group_id": group_user.id,
            }
        )
        group_followers = group_rule._resolve_followers(
            requester=actor_user,
            approvers=self.env["res.users"],
            record=partner,
        )
        self.assertIn(actor_user, group_followers, "Group rule should resolve to group users")

        field_rule = self.env["workflow.follower.rule"].create(
            {
                "name": "Field",
                "definition_version_id": self.version.id,
                "follower_type": "field",
                "field_path": "user_id",
            }
        )
        field_followers = field_rule._resolve_followers(
            requester=actor_user,
            approvers=self.env["res.users"],
            record=partner,
        )
        self.assertIn(actor_user, field_followers, "Field rule should resolve user_id from target record")

    def test_follower_rule_cascades_on_version_delete(self):
        definition = self.env["workflow.definition"].create(
            {
                "name": "Cascade Follower Definition",
                "definition_key": "cascade_follower",
            }
        )
        version = self.env["workflow.definition.version"].create(
            {
                "definition_id": definition.id,
                "bpmn_xml": "<xml/>",
            }
        )
        rule = self.env["workflow.follower.rule"].create(
            {
                "name": "Cascade Follower",
                "definition_version_id": version.id,
                "follower_type": "requester",
            }
        )
        version.unlink()
        self.assertFalse(
            self.env["workflow.follower.rule"].search([("id", "=", rule.id)]),
            "Follower rule should be deleted when definition version is deleted",
        )
