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

    def test_binding_action_window_contract(self):
        action = self.env.ref("dynamic_approval_core.action_workflow_binding")

        self.assertEqual(action.res_model, "workflow.binding", "Binding action must target workflow.binding")
        self.assertEqual(action.view_mode, "list,form", "Binding action must use list/form mode")
        self.assertIn(
            self.group_designer,
            action.group_ids,
            "Binding action must be restricted to workflow designer users",
        )

    def test_binding_form_has_header_scopes_callback_and_warning_pages(self):
        form_view = self.env.ref("dynamic_approval_core.view_workflow_binding_form")
        root = etree.fromstring(form_view.arch_db.encode())

        validate_buttons = root.xpath("//header//button[@name='action_validate' and @type='object']")
        enable_buttons = root.xpath("//header//button[@name='action_enable' and @type='object']")
        disable_buttons = root.xpath("//header//button[@name='action_disable' and @type='object']")
        self.assertTrue(validate_buttons, "Binding form must expose Validate in the header")
        self.assertTrue(enable_buttons, "Binding form must expose Enable in the header")
        self.assertTrue(disable_buttons, "Binding form must expose Disable in the header")

        stat_buttons = root.xpath("//div[contains(@class, 'oe_button_box')]//button[contains(@class, 'oe_stat_button')]")
        self.assertTrue(stat_buttons, "Binding form must include a stat button box")

        scope_list_nodes = root.xpath("//page[@string='Scopes']//field[@name='scope_ids']/list")
        self.assertTrue(scope_list_nodes, "Binding form must render inline rollout scopes")
        self.assertEqual(
            scope_list_nodes[0].get("editable"),
            "bottom",
            "Scope inline list must be editable from the bottom",
        )
        scope_fields = [field.get("name") for field in scope_list_nodes[0].xpath("./field")]
        self.assertEqual(
            scope_fields,
            ["scope_type", "scope_company_id", "scope_group_id", "scope_domain"],
            "Scope inline list must match the OMB field order",
        )

        callback_page = root.xpath("//page[@string='Callback']")
        self.assertTrue(callback_page, "Binding form must include a Callback page")
        callback_fields = callback_page[0].xpath(".//field")
        callback_field_names = [field.get("name") for field in callback_fields]
        self.assertEqual(
            callback_field_names,
            [
                "callback_model",
                "callback_method",
                "callback_execution_principal",
                "callback_service_user_id",
                "callback_idempotency_policy",
            ],
            "Callback page must expose the full callback configuration contract",
        )
        service_user_field = callback_page[0].xpath(".//field[@name='callback_service_user_id']")
        self.assertTrue(service_user_field, "Callback page must include callback_service_user_id")
        self.assertEqual(
            service_user_field[0].get("invisible"),
            "callback_execution_principal != 'service_principal'",
            "Service user field must be hidden unless service principal is selected",
        )

        warning_field = root.xpath("//page[@string='Warning']//field[@name='ui_warning_message']")
        self.assertTrue(warning_field, "Binding form must include the warning message page")

    def test_binding_list_and_search_views_match_omb_contract(self):
        list_view = self.env.ref("dynamic_approval_core.view_workflow_binding_list")
        list_root = etree.fromstring(list_view.arch_db.encode())
        actual_columns = [
            (field.get("name"), field.get("widget"))
            for field in list_root.xpath("//list/field")
        ]
        self.assertEqual(
            actual_columns,
            [
                ("name", None),
                ("definition_id", None),
                ("target_model", None),
                ("target_action_method", None),
                ("enforcement_mode", "badge"),
                ("is_active", "boolean_toggle"),
                ("company_id", None),
            ],
            "Binding list view columns must match the OMB contract and widgets",
        )

        search_view = self.env.ref("dynamic_approval_core.view_workflow_binding_search")
        search_root = etree.fromstring(search_view.arch_db.encode())
        search_field_names = [field.get("name") for field in search_root.xpath("//search/field")]
        self.assertEqual(
            search_field_names,
            ["name", "target_model", "definition_id", "enforcement_mode"],
            "Binding search view must expose the expected search fields",
        )
        active_filter = search_root.xpath("//filter[@name='active_bindings']")
        self.assertTrue(active_filter, "Binding search must include the Active filter")
        self.assertEqual(
            active_filter[0].get("domain"),
            "[('is_active', '=', True)]",
            "Active filter must target enabled bindings",
        )
        compliance_filter = search_root.xpath("//filter[@name='compliance_critical']")
        self.assertTrue(compliance_filter, "Binding search must include the compliance-critical filter")
        group_by_filter = search_root.xpath("//filter[@name='group_by_enforcement_mode']")
        self.assertTrue(group_by_filter, "Binding search must include the enforcement group-by filter")
        self.assertEqual(
            group_by_filter[0].get("context"),
            "{'group_by': 'enforcement_mode'}",
            "Binding search group-by filter must group on enforcement_mode",
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
        binding_action = self.env.ref("dynamic_approval_core.action_workflow_binding")
        self.assertEqual(definitions_menu.action, definition_action, "Definitions menu must open definition action")
        self.assertEqual(bindings_menu.action, binding_action, "Bindings menu must open binding action")
