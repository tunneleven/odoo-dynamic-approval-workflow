from psycopg2.errors import UniqueViolation

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestWorkflowBinding(TransactionCase):
    """Tests for workflow.binding and workflow.binding.scope."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.definition = cls.env["workflow.definition"].create(
            {
                "name": "Binding Test WF",
                "definition_key": "binding_test_wf",
            }
        )
        cls.other_company = cls.env["res.company"].create({"name": "Binding Other Company"})
        cls.service_user = cls.env.ref("base.user_admin")
        cls.base_group_user = cls.env.ref("base.group_user")

    def setUp(self):
        super().setUp()
        self._sequence = 0

    def _new_binding_vals(self, **overrides):
        self._sequence += 1
        values = {
            "name": f"Binding {self._sequence}",
            "definition_id": self.definition.id,
            "target_model": "res.partner",
            "target_action_method": f"action_binding_{self._sequence}",
        }
        values.update(overrides)
        return values

    def _create_binding(self, **overrides):
        return self.env["workflow.binding"].create(self._new_binding_vals(**overrides))

    def test_binding_defaults_match_omb_contract(self):
        binding = self._create_binding()
        self.assertEqual(binding.enforcement_mode, "orm_enforced")
        self.assertFalse(binding.is_active)
        self.assertEqual(binding.binding_priority, 100)
        self.assertEqual(binding.callback_execution_principal, "request_actor")
        self.assertEqual(binding.callback_idempotency_policy, "strict_once")
        self.assertEqual(binding.interceptor_config_revision, 0)

    def test_unique_model_method_company_constraint(self):
        values = self._new_binding_vals(
            name="Unique Source Binding",
            target_action_method="action_unique_source",
        )
        self.env["workflow.binding"].create(values)

        with self.cr.savepoint(), self.assertRaises(UniqueViolation):
            self.env["workflow.binding"].create({**values, "name": "Duplicate Source Binding"})

    def test_target_model_must_exist(self):
        with self.assertRaises(ValidationError):
            self._create_binding(target_model="x_model_does_not_exist")

    def test_target_and_callback_method_regex(self):
        invalid_methods = ["ActionConfirm", "1start", "action-confirm", "action confirm"]
        for method_name in invalid_methods:
            with self.assertRaises(ValidationError):
                self._create_binding(target_action_method=method_name)

        for callback_method in invalid_methods:
            with self.assertRaises(ValidationError):
                self._create_binding(
                    callback_model="res.partner",
                    callback_method=callback_method,
                )

    def test_ui_only_forbidden_when_compliance_critical(self):
        with self.assertRaises(ValidationError):
            self._create_binding(
                enforcement_mode="ui_only",
                compliance_critical=True,
            )

    def test_callback_model_and_method_must_be_pair(self):
        with self.assertRaises(ValidationError):
            self._create_binding(callback_model="res.partner")

        with self.assertRaises(ValidationError):
            self._create_binding(callback_method="write")

    def test_service_principal_requires_service_user(self):
        with self.assertRaises(ValidationError):
            self._create_binding(
                callback_model="res.partner",
                callback_method="write",
                callback_execution_principal="service_principal",
            )

        binding = self._create_binding(
            callback_model="res.partner",
            callback_method="write",
            callback_execution_principal="service_principal",
            callback_service_user_id=self.service_user.id,
        )
        self.assertEqual(binding.callback_service_user_id, self.service_user)

    def test_callback_model_https_url_validation(self):
        with self.assertRaises(ValidationError):
            self._create_binding(
                callback_model="http://example.com/callback",
                callback_method="sync",
            )

        binding = self._create_binding(
            callback_model="https://example.com/callback",
            callback_method="sync",
        )
        self.assertEqual(binding.callback_model, "https://example.com/callback")

    def test_action_validate_enable_disable_and_revision(self):
        binding = self._create_binding(
            callback_model="res.partner",
            callback_method="write",
        )

        validation_result = binding.action_validate()
        self.assertEqual(validation_result.get("binding_id"), binding.id)
        self.assertTrue(validation_result.get("valid"))

        self.assertIs(binding.action_enable(), True)
        self.assertTrue(binding.is_active)
        self.assertEqual(binding.interceptor_config_revision, 1)

        self.assertIs(binding.action_disable(), True)
        self.assertFalse(binding.is_active)
        self.assertEqual(binding.interceptor_config_revision, 2)

        binding.write({"binding_priority": 300})
        self.assertEqual(binding.interceptor_config_revision, 3)

    def test_execute_callback_resolves_execution_principal(self):
        request_actor_binding = self._create_binding(
            callback_model="res.partner",
            callback_method="write",
        )
        request_result = request_actor_binding.execute_callback(
            instance_id=11,
            payload={},
            idempotency_key="request-actor-key",
        )
        self.assertEqual(request_result["effective_execution_principal"], "request_actor")
        self.assertEqual(request_result["effective_execution_user_id"], self.env.user.id)

        approver_actor_binding = self._create_binding(
            callback_model="res.partner",
            callback_method="write",
            callback_execution_principal="approver_actor",
        )
        with self.assertRaises(ValidationError):
            approver_actor_binding.execute_callback(
                instance_id=12,
                payload={},
                idempotency_key="approver-missing-user",
            )

        approver_result = approver_actor_binding.execute_callback(
            instance_id=12,
            payload={"effective_actor_user_id": self.service_user.id},
            idempotency_key="approver-user-present",
        )
        self.assertEqual(approver_result["effective_execution_principal"], "approver_actor")
        self.assertEqual(approver_result["effective_execution_user_id"], self.service_user.id)

        service_principal_binding = self._create_binding(
            callback_model="res.partner",
            callback_method="write",
            callback_execution_principal="service_principal",
            callback_service_user_id=self.service_user.id,
        )
        service_result = service_principal_binding.execute_callback(
            instance_id=13,
            payload={},
            idempotency_key="service-principal-key",
        )
        self.assertEqual(service_result["effective_execution_principal"], "service_principal")
        self.assertEqual(service_result["effective_execution_user_id"], self.service_user.id)

    def test_enabled_binding_target_fields_are_immutable_without_context_bypass(self):
        binding = self._create_binding()
        binding.action_enable()

        with self.assertRaises(ValidationError):
            binding.with_context(allow_active_target_write=True).write(
                {
                    "target_model": "res.users",
                }
            )

    def test_scope_value_required_by_scope_type(self):
        binding = self._create_binding()

        with self.assertRaises(ValidationError):
            self.env["workflow.binding.scope"].create(
                {
                    "binding_id": binding.id,
                    "scope_type": "company",
                }
            )

        with self.assertRaises(ValidationError):
            self.env["workflow.binding.scope"].create(
                {
                    "binding_id": binding.id,
                    "scope_type": "group",
                }
            )

        with self.assertRaises(ValidationError):
            self.env["workflow.binding.scope"].create(
                {
                    "binding_id": binding.id,
                    "scope_type": "domain",
                }
            )

    def test_scope_domain_json_and_field_validation(self):
        binding = self._create_binding(target_model="res.partner")

        with self.assertRaises(ValidationError):
            self.env["workflow.binding.scope"].create(
                {
                    "binding_id": binding.id,
                    "scope_type": "domain",
                    "scope_domain": "not-json",
                }
            )

        with self.assertRaises(ValidationError):
            self.env["workflow.binding.scope"].create(
                {
                    "binding_id": binding.id,
                    "scope_type": "domain",
                    "scope_domain": "{}",
                }
            )

        with self.assertRaises(ValidationError):
            self.env["workflow.binding.scope"].create(
                {
                    "binding_id": binding.id,
                    "scope_type": "domain",
                    "scope_domain": '[["missing_field", "=", 1]]',
                }
            )

        valid_domain_scope = self.env["workflow.binding.scope"].create(
            {
                "binding_id": binding.id,
                "scope_type": "domain",
                "scope_domain": '[["is_company", "=", true]]',
            }
        )
        self.assertTrue(valid_domain_scope.id)

    def test_scope_company_related_and_revision_increment(self):
        binding = self._create_binding()
        self.assertEqual(binding.interceptor_config_revision, 0)

        scope = self.env["workflow.binding.scope"].create(
            {
                "binding_id": binding.id,
                "scope_type": "company",
                "scope_company_id": self.other_company.id,
            }
        )
        self.assertEqual(scope.company_id, binding.company_id)
        self.assertEqual(binding.interceptor_config_revision, 1)

        scope.write({"scope_company_id": binding.company_id.id})
        self.assertEqual(binding.interceptor_config_revision, 2)

        scope.unlink()
        self.assertEqual(binding.interceptor_config_revision, 3)

    def test_scope_group_scope_valid(self):
        binding = self._create_binding()
        group_scope = self.env["workflow.binding.scope"].create(
            {
                "binding_id": binding.id,
                "scope_type": "group",
                "scope_group_id": self.base_group_user.id,
            }
        )
        self.assertEqual(group_scope.scope_group_id, self.base_group_user)
