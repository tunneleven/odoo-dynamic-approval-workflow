from lxml import etree

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWorkflowDefinitionViews(TransactionCase):
    """Validate workflow definition views, actions, and menu contracts."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group_approver = cls.env.ref("dynamic_approval_core.group_workflow_approver")
        cls.group_designer = cls.env.ref("dynamic_approval_core.group_workflow_designer")
        cls.group_admin = cls.env.ref("dynamic_approval_core.group_workflow_admin")

    def test_definition_action_window_contract(self):
        action = self.env.ref("dynamic_approval_core.action_workflow_definition")

        self.assertEqual(action.res_model, "workflow.definition", "Definition action must target workflow.definition")
        self.assertEqual(action.view_mode, "list,form", "Definition action must use list/form mode")
        self.assertIn(
            self.group_designer,
            action.group_ids,
            "Definition action must be restricted to workflow designer users",
        )

    def test_definition_form_has_description_and_inline_versions(self):
        form_view = self.env.ref("dynamic_approval_core.view_workflow_definition_form")
        root = etree.fromstring(form_view.arch_db.encode())

        description_fields = root.xpath("//page[@string='Description']//field[@name='description' and @widget='html']")
        self.assertTrue(description_fields, "Definition form must render description with html widget")

        version_list_nodes = root.xpath("//page[@string='Versions']//field[@name='version_ids']/list")
        self.assertTrue(version_list_nodes, "Definition form must show inline version list inside Versions page")

        actual_fields = [field.get("name") for field in version_list_nodes[0].xpath("./field")]
        expected_fields = [
            "version",
            "state",
            "effective_from_utc",
            "effective_to_utc",
            "published_at_utc",
        ]
        self.assertEqual(
            actual_fields,
            expected_fields,
            "Inline version list must match the OMB field order",
        )

    def test_definition_search_has_company_field_and_my_company_filter(self):
        search_view = self.env.ref("dynamic_approval_core.view_workflow_definition_search")
        root = etree.fromstring(search_view.arch_db.encode())

        self.assertTrue(root.xpath("//field[@name='company_id']"), "Definition search must include company_id field")
        my_company_filter = root.xpath("//filter[@name='my_company']")
        self.assertTrue(my_company_filter, "Definition search must include a My Company filter")
        self.assertEqual(
            my_company_filter[0].get("domain"),
            "[('company_id', '=', context.get('allowed_company_ids', [False])[0])]",
            "My Company filter domain must match OMB",
        )

    def test_root_menu_tree_groups_sequences_and_actions(self):
        root_menu = self.env.ref("dynamic_approval_core.menu_workflow_root")
        definitions_menu = self.env.ref("dynamic_approval_core.menu_workflow_definitions")
        bindings_menu = self.env.ref("dynamic_approval_core.menu_workflow_bindings")
        my_tasks_menu = self.env.ref("dynamic_approval_core.menu_workflow_my_tasks")
        instances_menu = self.env.ref("dynamic_approval_core.menu_workflow_instances")
        incidents_menu = self.env.ref("dynamic_approval_core.menu_workflow_incidents")
        webhooks_menu = self.env.ref("dynamic_approval_core.menu_workflow_webhooks")
        config_menu = self.env.ref("dynamic_approval_core.menu_workflow_config")

        self.assertEqual(root_menu.sequence, 50, "Root menu sequence must be 50")
        self.assertIn(self.group_approver, root_menu.group_ids, "Root menu must be visible to approvers")

        self.assertEqual(definitions_menu.parent_id, root_menu, "Definitions must be a direct child of Approvals")
        self.assertEqual(definitions_menu.sequence, 10, "Definitions menu sequence must be 10")
        self.assertIn(self.group_designer, definitions_menu.group_ids, "Definitions menu must require designer group")

        self.assertEqual(bindings_menu.parent_id, root_menu, "Bindings must be a direct child of Approvals")
        self.assertEqual(bindings_menu.sequence, 20, "Bindings menu sequence must be 20")
        self.assertIn(self.group_designer, bindings_menu.group_ids, "Bindings menu must require designer group")

        self.assertEqual(my_tasks_menu.parent_id, root_menu, "My Tasks must be a direct child of Approvals")
        self.assertEqual(my_tasks_menu.sequence, 30, "My Tasks menu sequence must be 30")
        self.assertIn(self.group_approver, my_tasks_menu.group_ids, "My Tasks menu must require approver group")

        self.assertEqual(instances_menu.parent_id, root_menu, "Instances must be a direct child of Approvals")
        self.assertEqual(instances_menu.sequence, 40, "Instances menu sequence must be 40")
        self.assertIn(self.group_approver, instances_menu.group_ids, "Instances menu must require approver group")

        self.assertEqual(incidents_menu.parent_id, root_menu, "Incidents must be a direct child of Approvals")
        self.assertEqual(incidents_menu.sequence, 50, "Incidents menu sequence must be 50")
        self.assertIn(self.group_admin, incidents_menu.group_ids, "Incidents menu must require admin group")

        self.assertEqual(webhooks_menu.parent_id, root_menu, "Webhooks must be a direct child of Approvals")
        self.assertEqual(webhooks_menu.sequence, 60, "Webhooks menu sequence must be 60")
        self.assertIn(self.group_admin, webhooks_menu.group_ids, "Webhooks menu must require admin group")

        self.assertEqual(config_menu.parent_id, root_menu, "Configuration must be a direct child of Approvals")
        self.assertEqual(config_menu.sequence, 90, "Configuration menu sequence must be 90")
        self.assertIn(self.group_admin, config_menu.group_ids, "Configuration menu must require admin group")

        definition_action = self.env.ref("dynamic_approval_core.action_workflow_definition")
        self.assertEqual(definitions_menu.action, definition_action, "Definitions menu must open definition action")
