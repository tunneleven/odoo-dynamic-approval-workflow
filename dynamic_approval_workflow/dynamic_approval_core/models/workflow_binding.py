import re
from urllib.parse import urlparse

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class WorkflowBinding(models.Model):
    """Binds a workflow definition to a target model/action."""

    _name = "workflow.binding"
    _description = "Workflow Binding"
    _inherit = ["mail.thread"]
    _order = "target_model, target_action_method"

    _method_name_regex = re.compile(r"^[a-z_][a-z0-9_]*$")
    _config_revision_fields = frozenset(
        {
            "definition_id",
            "target_model",
            "target_action_method",
            "enforcement_mode",
            "compliance_critical",
            "callback_model",
            "callback_method",
            "callback_execution_principal",
            "callback_service_user_id",
            "callback_idempotency_policy",
            "is_active",
            "binding_priority",
            "ui_warning_message",
            "company_id",
        }
    )

    name = fields.Char(size=128, required=True, tracking=True)
    definition_id = fields.Many2one(
        "workflow.definition",
        required=True,
        ondelete="restrict",
        index=True,
    )
    target_model = fields.Char(size=128, required=True, index=True)
    target_action_method = fields.Char(size=64, required=True, index=True)
    enforcement_mode = fields.Selection(
        [
            ("orm_enforced", "ORM Enforced"),
            ("hybrid", "Hybrid"),
            ("ui_only", "UI Only"),
        ],
        default="orm_enforced",
        required=True,
        index=True,
        tracking=True,
    )
    compliance_critical = fields.Boolean(default=False)
    callback_model = fields.Char(size=128)
    callback_method = fields.Char(size=64)
    callback_execution_principal = fields.Selection(
        [
            ("request_actor", "Request Actor"),
            ("approver_actor", "Approver Actor"),
            ("service_principal", "Service Principal"),
        ],
        default="request_actor",
    )
    callback_service_user_id = fields.Many2one(
        "res.users",
        ondelete="restrict",
    )
    callback_idempotency_policy = fields.Selection(
        [
            ("strict_once", "Strict Once"),
            ("allow_safe_replay", "Allow Safe Replay"),
        ],
        default="strict_once",
    )
    is_active = fields.Boolean(default=False, tracking=True)
    binding_priority = fields.Integer(default=100)
    ui_warning_message = fields.Char(size=255)
    company_id = fields.Many2one(
        "res.company",
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    scope_ids = fields.One2many(
        "workflow.binding.scope",
        "binding_id",
        string="Scopes",
    )
    interceptor_config_revision = fields.Integer(
        default=0,
        readonly=True,
    )

    _unique_model_action_company = models.Constraint(
        "UNIQUE(target_model, target_action_method, company_id)",
        "Binding must be unique per model, method, and company.",
    )

    @api.constrains("target_model")
    def _check_target_model_exists(self):
        for record in self:
            if not record._is_installed_model(record.target_model):
                raise ValidationError(
                    _("Target model '%s' is not installed.") % (record.target_model or "")
                )

    @api.constrains("enforcement_mode", "compliance_critical")
    def _check_ui_only_not_compliance(self):
        for record in self:
            if record.enforcement_mode == "ui_only" and record.compliance_critical:
                raise ValidationError(
                    _("Enforcement mode 'ui_only' is forbidden for compliance critical bindings.")
                )

    @api.constrains("callback_model", "callback_method")
    def _check_callback_pair(self):
        for record in self:
            if bool(record.callback_model) != bool(record.callback_method):
                raise ValidationError(
                    _("Callback model and callback method must both be set or both empty.")
                )
            if record.callback_model:
                record._validate_callback_model()

    @api.constrains("callback_execution_principal", "callback_service_user_id")
    def _check_service_principal_user(self):
        for record in self:
            if (
                record.callback_execution_principal == "service_principal"
                and not record.callback_service_user_id
            ):
                raise ValidationError(
                    _("Service principal requires a callback service user.")
                )

    @api.constrains("target_action_method", "callback_method")
    def _check_method_format(self):
        for record in self:
            if not self._method_name_regex.fullmatch(record.target_action_method or ""):
                raise ValidationError(
                    _("Target action method must match ^[a-z_][a-z0-9_]*$.")
                )
            if record.callback_method and not self._method_name_regex.fullmatch(record.callback_method):
                raise ValidationError(
                    _("Callback method must match ^[a-z_][a-z0-9_]*$.")
                )

    def _validate_callback_model(self):
        self.ensure_one()
        callback_target = self.callback_model or ""
        if self._looks_like_url(callback_target):
            if not self._is_https_url(callback_target):
                raise ValidationError(
                    _("Callback URL must use HTTPS.")
                )
            return

        if not self._is_installed_model(callback_target):
            raise ValidationError(
                _("Callback model '%s' is not installed.") % callback_target
            )

    def _is_installed_model(self, model_name):
        return bool(model_name) and model_name in self.env

    @staticmethod
    def _looks_like_url(value):
        return "://" in (value or "")

    @staticmethod
    def _is_https_url(value):
        parsed = urlparse(value or "")
        return parsed.scheme == "https" and bool(parsed.netloc)

    def action_validate(self):
        self.ensure_one()
        self._check_target_model_exists()
        self._check_ui_only_not_compliance()
        self._check_callback_pair()
        self._check_service_principal_user()
        self._check_method_format()
        return {
            "valid": True,
            "binding_id": self.id,
            "enforcement_mode": self.enforcement_mode,
        }

    def action_enable(self):
        for record in self:
            record.action_validate()
        self.write({"is_active": True})
        return True

    def action_disable(self):
        self.write({"is_active": False})
        return True

    def evaluate_gate(self, record_context):
        self.ensure_one()
        is_enforced = self.is_active and self.enforcement_mode in {"orm_enforced", "hybrid"}
        if self.enforcement_mode == "ui_only" and self.ui_warning_message:
            decision = "allow_with_warning"
        else:
            decision = "allow"
        return {
            "decision": decision,
            "enforced": is_enforced,
            "warning_message": self.ui_warning_message or "",
            "context": dict(record_context or {}),
        }

    def execute_callback(self, instance_id, payload, idempotency_key):
        self.ensure_one()
        if not self.callback_model or not self.callback_method:
            return {
                "status": "skipped",
                "reason": "callback_not_configured",
                "binding_id": self.id,
            }

        payload_data = dict(payload or {})
        callback_user = self._resolve_callback_execution_user(payload_data)

        if self._looks_like_url(self.callback_model):
            return {
                "status": "queued_external",
                "target_url": self.callback_model,
                "method": self.callback_method,
                "instance_id": instance_id,
                "idempotency_key": idempotency_key,
                "effective_execution_principal": self.callback_execution_principal,
                "effective_execution_user_id": callback_user.id,
            }

        callback_model = self.env[self.callback_model].with_user(callback_user)
        if not hasattr(callback_model, self.callback_method):
            raise ValidationError(
                _("Callback method '%s' does not exist on model '%s'.")
                % (self.callback_method, self.callback_model)
            )
        return {
            "status": "ready",
            "target_model": self.callback_model,
            "target_method": self.callback_method,
            "instance_id": instance_id,
            "payload": payload_data,
            "idempotency_key": idempotency_key,
            "effective_execution_principal": self.callback_execution_principal,
            "effective_execution_user_id": callback_user.id,
        }

    def _resolve_callback_execution_user(self, payload):
        self.ensure_one()
        principal = self.callback_execution_principal or "request_actor"

        if principal == "service_principal":
            callback_user = self.callback_service_user_id
            if not callback_user:
                raise ValidationError(
                    _("Service principal requires a callback service user.")
                )
        elif principal == "approver_actor":
            approver_user_id = payload.get("effective_actor_user_id")
            if not approver_user_id:
                raise ValidationError(
                    _("Approver actor callbacks require payload key 'effective_actor_user_id'.")
                )
            callback_user = self.env["res.users"].browse(approver_user_id).exists()
            if not callback_user:
                raise ValidationError(
                    _("Approver actor callback user '%s' does not exist.") % approver_user_id
                )
            if not callback_user.active:
                raise ValidationError(
                    _("Approver actor callback user '%s' is inactive.")
                    % callback_user.display_name
                )
        else:
            callback_user = self.env.user

        if principal == "service_principal" and not callback_user.active:
            raise ValidationError(
                _("Callback execution user '%s' is inactive.") % callback_user.display_name
            )

        return callback_user

    def _refresh_interceptor_patches(self):
        from .workflow_enforcement_interceptor import WorkflowEnforcementInterceptor

        WorkflowEnforcementInterceptor._apply_patches(self.env)

    def _register_hook(self):
        result = super()._register_hook()
        self._refresh_interceptor_patches()
        return result

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._refresh_interceptor_patches()
        return records

    def _increment_config_revision(self):
        for record in self:
            record.with_context(skip_binding_revision_increment=True).write(
                {"interceptor_config_revision": record.interceptor_config_revision + 1}
            )

    def write(self, vals):
        if (
            any(field in vals for field in ("target_model", "target_action_method"))
            and any(self.mapped("is_active"))
        ):
            raise ValidationError(
                _("Target model and action method are immutable once the binding is enabled.")
            )

        should_bump_revision = (
            not self.env.context.get("skip_binding_revision_increment")
            and bool(self._config_revision_fields.intersection(set(vals)))
            and set(vals) != {"interceptor_config_revision"}
        )

        result = super().write(vals)
        if should_bump_revision:
            self._increment_config_revision()
            self._refresh_interceptor_patches()
        return result

    def unlink(self):
        result = super().unlink()
        self._refresh_interceptor_patches()
        return result
