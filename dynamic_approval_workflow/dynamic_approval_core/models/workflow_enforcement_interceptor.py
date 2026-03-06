from functools import wraps
from threading import RLock

from odoo import _, fields, models

from ..exceptions import WorkflowGateBlockedError

class WorkflowEnforcementInterceptor(models.AbstractModel):
    """ORM enforcement interceptor — ``_patch_method`` wrapper logic.

    Wraps bound model methods at registry load time to enforce
    workflow gates across all channels (UI, RPC, import, cron, sudo).

    This is an abstract model; it does not create a database table.

    SDS: §7 ORM Interceptor Design
    SRS: FR-008, FR-090..FR-092  |  DFR: DFR-02-002..DFR-02-011
    ADR: ADR-002
    """

    _name = "workflow.enforcement.interceptor"
    _description = "Workflow Enforcement Interceptor"
    _register = False
    _auto = False

    _patch_lock = RLock()
    _patched_methods = {}

    @classmethod
    def _apply_patches(cls, env):
        """Patch all active `orm_enforced`/`hybrid` binding methods."""
        with cls._patch_lock:
            cls._remove_patches(env)

            bindings = env["workflow.binding"].sudo().search(
                [
                    ("is_active", "=", True),
                    ("enforcement_mode", "in", ("orm_enforced", "hybrid")),
                ]
            )
            for binding in bindings:
                model_name = binding.target_model
                method_name = binding.target_action_method
                if not model_name or not method_name or model_name not in env:
                    continue

                model_class = type(env[model_name])
                original_method = getattr(model_class, method_name, None)
                if not callable(original_method):
                    continue

                patch_key = (model_name, method_name)
                if patch_key in cls._patched_methods:
                    continue

                wrapper = cls._build_wrapper(model_name, method_name, original_method)
                cls._patch_method(model_class, method_name, wrapper)
                cls._patched_methods[patch_key] = {
                    "model_class": model_class,
                    "original_method": original_method,
                }

    @classmethod
    def _remove_patches(cls, _env):
        """Revert previously patched methods to their original callables."""
        with cls._patch_lock:
            for (_, method_name), patch_info in list(cls._patched_methods.items()):
                cls._unpatch_method(
                    patch_info["model_class"],
                    method_name,
                    patch_info["original_method"],
                )
            cls._patched_methods = {}

    @classmethod
    def _build_wrapper(cls, model_name, method_name, original_method):
        """Build the interception wrapper for one `(model, method)` pair."""

        @wraps(original_method)
        def _workflow_intercept_wrapper(recordset, *args, **kwargs):
            env = recordset.env
            if env.context.get("_workflow_bypass_token"):
                cls._log_gate_event(
                    env,
                    model_name,
                    method_name,
                    "allowed",
                    reason_code="bypass_token",
                    recordset=recordset,
                )
                return original_method(recordset, *args, **kwargs)

            channel = env.context.get("_workflow_channel") or "rpc"
            company_id = env.company.id
            binding = cls._resolve_binding(env, model_name, method_name, company_id)
            if not binding:
                cls._record_incident(
                    env,
                    reason_code="path_uncovered",
                    model_name=model_name,
                    method_name=method_name,
                    details="No active binding resolved for patched path.",
                )
                raise WorkflowGateBlockedError(
                    _("Workflow interception path is uncovered. Action is blocked.")
                )

            record_context = {
                "model": model_name,
                "res_ids": list(recordset.ids),
                "action_method": method_name,
                "actor_user_id": env.user.id,
                "company_id": company_id,
                "channel": channel,
                "request_id": env.context.get("request_id"),
            }

            try:
                gate_result = binding.evaluate_gate(record_context)
            except Exception as err:
                cls._record_incident(
                    env,
                    reason_code="interceptor_error",
                    model_name=model_name,
                    method_name=method_name,
                    details=str(err),
                )
                raise WorkflowGateBlockedError(
                    _("Workflow gate evaluation failed. Action is blocked.")
                ) from err

            state = cls._normalize_gate_state(gate_result)
            reason_code = cls._extract_reason_code(gate_result)
            policy_message = cls._extract_policy_message(gate_result)

            cls._log_gate_event(
                env,
                model_name,
                method_name,
                state,
                reason_code=reason_code,
                policy_message=policy_message,
                binding_id=binding.id,
                recordset=recordset,
                channel=channel,
            )

            if state == "blocked":
                raise WorkflowGateBlockedError(
                    policy_message or _("Action is blocked by workflow policy.")
                )

            if state not in {"allowed", "allowed_with_warning"}:
                cls._record_incident(
                    env,
                    reason_code="invalid_gate_state",
                    model_name=model_name,
                    method_name=method_name,
                    details="Gate state '%s' is unsupported." % state,
                )
                raise WorkflowGateBlockedError(
                    _("Workflow gate returned invalid state. Action is blocked.")
                )

            return original_method(recordset, *args, **kwargs)

        return _workflow_intercept_wrapper

    @staticmethod
    def _resolve_binding(env, model_name, method_name, company_id):
        """Resolve active binding by model + method + company context."""
        return env["workflow.binding"].sudo().search(
            [
                ("is_active", "=", True),
                ("target_model", "=", model_name),
                ("target_action_method", "=", method_name),
                ("enforcement_mode", "in", ("orm_enforced", "hybrid")),
                ("company_id", "in", [company_id, False]),
            ],
            order="binding_priority desc, id asc",
            limit=1,
        )

    @staticmethod
    def _patch_method(model_class, method_name, wrapper_method):
        patch_method = getattr(model_class, "_patch_method", None)
        if callable(patch_method):
            patch_method(method_name, wrapper_method)
            return
        setattr(model_class, method_name, wrapper_method)

    @staticmethod
    def _unpatch_method(model_class, method_name, original_method):
        revert_method = getattr(model_class, "_revert_method", None)
        if callable(revert_method):
            revert_method(method_name)
            return
        setattr(model_class, method_name, original_method)

    @staticmethod
    def _normalize_gate_state(gate_result):
        if not isinstance(gate_result, dict):
            return "blocked"
        state = gate_result.get("state") or gate_result.get("decision") or "blocked"
        if state == "allow":
            return "allowed"
        if state == "allow_with_warning":
            return "allowed_with_warning"
        return state

    @staticmethod
    def _extract_reason_code(gate_result):
        if not isinstance(gate_result, dict):
            return "invalid_result"
        return gate_result.get("reason_code") or "gate_evaluated"

    @staticmethod
    def _extract_policy_message(gate_result):
        if not isinstance(gate_result, dict):
            return _("Workflow gate response is invalid.")
        return (
            gate_result.get("policy_message")
            or gate_result.get("warning_message")
            or ""
        )

    @classmethod
    def _log_gate_event(
        cls,
        env,
        model_name,
        method_name,
        state,
        reason_code,
        recordset,
        policy_message="",
        binding_id=False,
        channel="rpc",
    ):
        payload = {
            "state": state,
            "reason_code": reason_code,
            "policy_message": policy_message,
            "binding_id": binding_id,
            "model": model_name,
            "method": method_name,
            "res_ids": list(recordset.ids),
            "channel": channel,
            "actor_user_id": env.user.id,
        }
        env["workflow.audit.event"].sudo().with_context(
            _workflow_bypass_token="interceptor_audit",
        ).log_event(
            "workflow.gate.evaluated",
            cls._build_object_ref(model_name, recordset),
            payload=payload,
            correlation_id=env.context.get("request_id"),
        )

    @staticmethod
    def _record_incident(env, reason_code, model_name, method_name, details):
        env["workflow.incident"].sudo().with_context(
            _workflow_bypass_token="interceptor_incident",
        ).create(
            {
                "category": "enforcement_failure",
                "severity": "critical",
                "reason_code": reason_code,
                "description": (
                    "Interceptor fail-closed on %s.%s: %s"
                    % (model_name, method_name, details)
                ),
                "opened_at_utc": fields.Datetime.now(),
                "company_id": env.company.id,
            }
        )

    @staticmethod
    def _build_object_ref(model_name, recordset):
        res_id_str = ",".join(map(str, recordset.ids)) or "0"
        return "%s,%s" % (model_name, res_id_str)
