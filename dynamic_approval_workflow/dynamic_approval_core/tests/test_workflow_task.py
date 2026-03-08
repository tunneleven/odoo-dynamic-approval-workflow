from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWorkflowApproverResolution(TransactionCase):
    """Tests for workflow.approver.resolution."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.base_group_user = cls.env.ref("base.group_user")
        cls.workflow_privilege = cls.env.ref("dynamic_approval_core.res_groups_privilege_workflow")
        cls.approver_group = cls.env["res.groups"].create(
            {
                "name": "Workflow Resolution Test Group",
                "privilege_id": cls.workflow_privilege.id,
            }
        )
        cls.requester_user = cls._create_user("requester_user", [cls.base_group_user.id])
        cls.fixed_user = cls._create_user("fixed_user", [cls.base_group_user.id])
        cls.group_user = cls._create_user(
            "group_user",
            [cls.base_group_user.id, cls.approver_group.id],
        )
        cls.field_user = cls._create_user("field_user", [cls.base_group_user.id])
        cls.fallback_user = cls._create_user("fallback_user", [cls.base_group_user.id])
        cls.definition = cls.env["workflow.definition"].create(
            {
                "name": "Approver Resolution Workflow",
                "definition_key": "approver_resolution_wf",
            }
        )
        cls.definition_version = cls.env["workflow.definition.version"].create(
            {
                "definition_id": cls.definition.id,
                "bpmn_xml": "<definitions/>",
            }
        )
        cls.partner_with_user = cls.field_user.partner_id
        cls.partner_without_user = cls.env["res.partner"].create(
            {
                "name": "Partner Without User",
            }
        )
        cls.instance_with_user = cls.env["workflow.instance"].create(
            {
                "definition_id": cls.definition.id,
                "definition_version_id": cls.definition_version.id,
                "res_model": "res.partner",
                "res_id": cls.partner_with_user.id,
                "requester_id": cls.requester_user.id,
            }
        )
        cls.instance_without_user = cls.env["workflow.instance"].create(
            {
                "definition_id": cls.definition.id,
                "definition_version_id": cls.definition_version.id,
                "res_model": "res.partner",
                "res_id": cls.partner_without_user.id,
                "requester_id": cls.requester_user.id,
            }
        )

    @classmethod
    def _create_user(cls, name_slug, group_ids):
        """Create an internal user for workflow tests."""
        return cls.env["res.users"].with_context(no_reset_password=True).create(
            {
                "name": name_slug.replace("_", " ").title(),
                "login": f"{name_slug}@example.com",
                "email": f"{name_slug}@example.com",
                "group_ids": [(6, 0, group_ids)],
                "company_id": cls.company.id,
                "company_ids": [(6, 0, [cls.company.id])],
            }
        )

    def _new_rule_vals(self, **overrides):
        """Build approver-resolution values with overridable defaults."""
        values = {
            "name": "Resolution Rule",
            "definition_version_id": self.definition_version.id,
            "node_id": "UserTask_1",
            "resolution_type": "user",
            "user_ids": [(6, 0, [self.fixed_user.id])],
        }
        values.update(overrides)
        return values

    def test_create_requires_source_specific_fields(self):
        """Model creation must enforce source-specific requirements."""
        with self.assertRaises(ValidationError):
            self.env["workflow.approver.resolution"].create(
                self._new_rule_vals(
                    resolution_type="user",
                    user_ids=[(6, 0, [])],
                )
            )

        with self.assertRaises(ValidationError):
            self.env["workflow.approver.resolution"].create(
                self._new_rule_vals(
                    resolution_type="group",
                    user_ids=[(5, 0, 0)],
                    group_id=False,
                )
            )

        with self.assertRaises(ValidationError):
            self.env["workflow.approver.resolution"].create(
                self._new_rule_vals(
                    resolution_type="field",
                    user_ids=[(5, 0, 0)],
                    field_path=False,
                )
            )

    def test_resolve_approvers_returns_named_users_deterministically(self):
        """TC-FR-031-001: fixed users resolve in deterministic order."""
        rule = self.env["workflow.approver.resolution"].create(
            self._new_rule_vals(
                user_ids=[(6, 0, [self.fallback_user.id, self.fixed_user.id])],
            )
        )

        approvers = rule.resolve_approvers(self.instance_with_user.id)

        self.assertEqual(
            approvers.ids,
            sorted([self.fixed_user.id, self.fallback_user.id]),
            "Named-user resolution must return the configured users in deterministic order.",
        )

    def test_resolve_approvers_returns_group_members(self):
        """TC-FR-031-002: group rules resolve group members."""
        rule = self.env["workflow.approver.resolution"].create(
            self._new_rule_vals(
                resolution_type="group",
                user_ids=[(5, 0, 0)],
                group_id=self.approver_group.id,
            )
        )

        approvers = rule.resolve_approvers(self.instance_with_user.id)

        self.assertEqual(
            approvers.ids,
            [self.group_user.id],
            "Group resolution must expand to the configured group's users.",
        )

    def test_resolve_approvers_returns_field_path_user(self):
        """Record-field rules resolve users from the workflow target record."""
        rule = self.env["workflow.approver.resolution"].create(
            self._new_rule_vals(
                resolution_type="field",
                user_ids=[(5, 0, 0)],
                field_path="user_ids",
            )
        )

        approvers = rule.resolve_approvers(self.instance_with_user.id)

        self.assertEqual(
            approvers.ids,
            [self.field_user.id],
            "Field-path resolution must return the user referenced on the business record.",
        )

    def test_resolve_approvers_uses_sequence_priority_for_multiple_rules(self):
        """Multiple rules must resolve in sequence order with duplicate collapse."""
        later_rule = self.env["workflow.approver.resolution"].create(
            self._new_rule_vals(
                name="Later Rule",
                sequence=20,
                user_ids=[(6, 0, [self.fixed_user.id])],
            )
        )
        earlier_rule = self.env["workflow.approver.resolution"].create(
            self._new_rule_vals(
                name="Earlier Rule",
                sequence=10,
                resolution_type="group",
                user_ids=[(5, 0, 0)],
                group_id=self.approver_group.id,
            )
        )

        approvers = (later_rule | earlier_rule).resolve_approvers(self.instance_with_user.id)

        self.assertEqual(
            approvers.ids,
            [self.group_user.id, self.fixed_user.id],
            "Sequence order must determine the combined approver order across matching rules.",
        )

    def test_fallback_named_users_used_when_primary_resolution_is_empty(self):
        """Configured fallback users must be used before incident creation."""
        incident_model = self.env["workflow.incident"]
        incident_count = incident_model.search_count([])
        rule = self.env["workflow.approver.resolution"].create(
            self._new_rule_vals(
                resolution_type="field",
                user_ids=[(5, 0, 0)],
                field_path="user_ids",
                fallback_type="fallback_named_users",
                fallback_user_ids=[(6, 0, [self.fallback_user.id])],
            )
        )

        approvers = rule.resolve_approvers(self.instance_without_user.id)

        self.assertEqual(
            approvers.ids,
            [self.fallback_user.id],
            "Fallback named users must resolve when the primary source returns no approvers.",
        )
        self.assertEqual(
            incident_model.search_count([]),
            incident_count,
            "Successful fallback must not create an incident.",
        )

    def test_no_approver_resolution_creates_incident(self):
        """TC-FR-074-001: empty resolution without fallback must create an incident."""
        rule = self.env["workflow.approver.resolution"].create(
            self._new_rule_vals(
                resolution_type="field",
                user_ids=[(5, 0, 0)],
                field_path="user_ids",
            )
        )

        approvers = rule.resolve_approvers(self.instance_without_user.id)
        incident = self.env["workflow.incident"].search(
            [
                ("instance_id", "=", self.instance_without_user.id),
                ("category", "=", "resolution_failure"),
                ("reason_code", "=", "no_approver_resolved"),
            ],
            order="id desc",
            limit=1,
        )

        self.assertFalse(approvers, "Approver resolution must return an empty set when no source or fallback matches.")
        self.assertTrue(incident, "An incident must be created when no approver can be resolved.")
        self.assertEqual(
            self.instance_without_user.state,
            "error_incident",
            "No-approver resolution must push the workflow instance into error_incident state.",
        )
