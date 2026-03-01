# SRS-02 Binding, Enforcement Modes, and Callback

Version: `v1.2-draft`
Date: `2026-02-28`
Parent: `dynamic_approval_workflow_srs_v1.3.md`
Master Traceability: `srs_00_master_traceability.md`

## 1. Purpose
Define detailed requirements for workflow binding to Odoo model/actions, generic server-side interception, multi-channel gate enforcement behavior, frontend hook contract, and post-approval callback execution.

## 2. Scope
In scope:
1. Binding configuration for model/action to workflow definition key.
2. Enforcement modes: `orm_enforced`, `hybrid`, and optional `ui_only`.
3. Generic server interceptor contract for server-side enforcement without per-model source edits.
4. Channel coverage rules for UI and non-UI invocation paths.
5. Gating state contract exposed to frontend hooks.
6. Requester withdraw and admin forced reassignment controls at binding level.
7. Post-approval callback selection, validation, execution principal, payload schema, idempotency, retry, and incident behavior.

Out of scope:
1. Workflow definition/version lifecycle (covered by `SRS-01`).
2. Runtime token orchestration and conditions (covered by `SRS-04`).
3. Human task assignment details (covered by `SRS-05`).

## 3. Inherited Requirement Coverage
- FR: `FR-007..012`, `FR-071`, `FR-072`, `FR-081`, `FR-090..095`
- NFR: `NFR-011`, `NFR-017`

## 4. Decomposed Detailed Requirements (DFR)
| DFR ID | Statement | Maps To |
|---|---|---|
| `DFR-02-001` | The system shall bind a workflow definition key to target `model` and target `action_method` through configuration records. | `FR-007` |
| `DFR-02-002` | The system shall block target action execution while required approvals are incomplete, unless a defined gate exception policy applies. | `FR-008` |
| `DFR-02-003` | The system shall integrate frontend hook state into form views without replacing native Odoo form elements by default. | `FR-009`, `FR-010`, `NFR-011` |
| `DFR-02-004` | Binding scope shall support rollout filters by company, group, and domain expression with deterministic precedence. | `FR-011` |
| `DFR-02-005` | Binding enable/disable shall be configurable without deleting workflow definitions or historical instances. | `FR-012` |
| `DFR-02-006` | Request creator withdraw/cancel capability shall be policy-driven and limited to eligible non-terminal states. | `FR-071` |
| `DFR-02-007` | Workflow Admin forced reassignment shall be allowed for pending tasks with mandatory reason and audit evidence. | `FR-072` |
| `DFR-02-008` | Frontend hook contract shall return explicit gating states: `blocked`, `allowed`, `allowed_with_warning`. | `FR-081` |
| `DFR-02-009` | Binding configuration shall support enforcement modes `orm_enforced`, `hybrid`, and optional `ui_only`, with `orm_enforced` as recommended default. | `FR-090` |
| `DFR-02-010` | In `orm_enforced` and `hybrid` modes, enforcement shall execute at target business method level and be consistent across UI and non-UI channels. | `FR-091`, `NFR-017` |
| `DFR-02-011` | `ui_only` mode shall require explicit risk acknowledgment and shall be blocked for `compliance_critical` bindings. | `FR-092` |
| `DFR-02-012` | Binding shall support selecting post-approval callback target (canonical `callback_model` + `callback_method`) executed on terminal approval. | `FR-093` |
| `DFR-02-013` | Callback configuration shall be validated before enable for model existence, callable existence, signature compatibility, ACL compatibility, payload compatibility, and idempotency policy compatibility. | `FR-094` |
| `DFR-02-014` | Callback execution failures shall create incidents, preserve audit evidence, and expose controlled retry/recovery actions. | `FR-095` |
| `DFR-02-015` | Generic server interceptor shall enforce configured `orm_enforced/hybrid` bindings without requiring per-model source edits. | `FR-091`, `NFR-017` |

## 5. Domain Objects (Conceptual)
1. `workflow.binding`
- Core binding record for model/action to definition key and enforcement mode.
2. `workflow.binding.scope`
- Rollout scope values (`company`, `group`, `domain`) and precedence metadata.
3. `workflow.binding.policy`
- Withdraw/reassign/gate exception rules and compliance tags.
4. `workflow.binding.callback`
- Callback target, validation status, execution principal policy, payload contract, and idempotency policy.
5. `workflow.binding.risk_ack`
- Explicit approval artifact for `ui_only` mode with actor, timestamp, and rationale.
6. `workflow.enforcement.interceptor`
- Runtime component that evaluates gate policy for server invocation paths.

## 6. Binding Configuration Contract
### 6.1 Field Specification Table
| Field | Odoo Type | Required | Default | Constraints / Notes |
|---|---|---|---|---|
| `binding_key` | `fields.Char(size=64)` | Yes | None | Unique with `owner_company_id`; immutable after create. |
| `owner_company_id` | `fields.Many2one('res.company')` | Yes | Current company | Company boundary for binding ownership and lookup. |
| `target_model` | `fields.Char(size=128)` | Yes | None | Must match installed model `_name`. |
| `target_action_method` | `fields.Char(size=64)` | Yes | None | Python method identifier regex `^[a-z_][a-z0-9_]*$`. |
| `definition_key` | `fields.Char(size=64)` | Yes | None | Must reference active definition key from `SRS-01`. |
| `enforcement_mode` | `fields.Selection` | Yes | `orm_enforced` | Allowed: `orm_enforced`, `hybrid`, `ui_only`. |
| `enabled` | `fields.Boolean` | Yes | `False` | Enable allowed only after validation succeeds. |
| `rollout_specificity` | `fields.Selection` | Yes | `global` | Allowed: `company`, `group`, `domain`, `global`. |
| `rollout_scope_company_id` | `fields.Many2one('res.company')` | Conditional | None | Required when `rollout_specificity=company`. |
| `rollout_scope_group_id` | `fields.Many2one('res.groups')` | Conditional | None | Required when `rollout_specificity=group`. |
| `rollout_scope_domain_json` | `fields.Json` | Conditional | None | Required when `rollout_specificity=domain`; validated per §6.3. |
| `binding_priority` | `fields.Integer` | Yes | `100` | Higher value wins within same specificity. |
| `compliance_tag` | `fields.Selection` | Yes | `normal` | Allowed: `normal`, `compliance_critical`. |
| `callback_model` | `fields.Char(size=128)` | Conditional | None | Required with `callback_method` when callback is enabled. |
| `callback_method` | `fields.Char(size=64)` | Conditional | None | Python method identifier regex `^[a-z_][a-z0-9_]*$`. |
| `callback_target_legacy` | `fields.Char(size=255)` | No | None | Optional compatibility input (`model.method`), normalized to canonical fields. |
| `callback_execution_principal` | `fields.Selection` | Conditional | `request_actor` | Allowed: `request_actor`, `approver_actor`, `service_principal`. |
| `callback_service_user_id` | `fields.Many2one('res.users')` | Conditional | None | Required when `callback_execution_principal=service_principal`. |
| `callback_idempotency_policy` | `fields.Selection` | Yes | `strict_once` | Allowed: `strict_once`, `allow_safe_replay`. |
| `withdraw_policy_json` | `fields.Json` | No | `{}` | Policy schema validated on save. |
| `force_reassign_policy_json` | `fields.Json` | No | `{}` | Policy schema validated on save. |
| `gate_exception_policy_json` | `fields.Json` | No | `{}` | Policy schema validated on save. |
| `ui_warning_message` | `fields.Char(size=255)` | No | None | Used by `allowed_with_warning` state. |

### 6.2 Referential and Validation Rules
1. `definition_key` must reference an existing definition governed by `SRS-01`.
2. Binding does not select version directly; version resolution is delegated to `SRS-01`.
3. Disabling a binding shall not delete or mutate historical runtime records.
4. `callback_target_legacy` input is accepted only as migration convenience; canonical storage is `callback_model` + `callback_method`.

### 6.3 Scope Payload Rules
1. `rollout_specificity = global` requires all scope fields null.
2. `rollout_specificity = company` requires `rollout_scope_company_id`.
3. `rollout_specificity = group` requires `rollout_scope_group_id`.
4. `rollout_specificity = domain` requires `rollout_scope_domain_json`.
5. Domain validation depth is mandatory:
- syntax parse validation;
- field-existence validation against `target_model`;
- safe-eval sandbox policy aligned with `SRS-07` (no callables/imports/env access).

## 7. Enforcement Modes and Channel Coverage
### 7.1 Modes
1. `orm_enforced`
- Gate executes in server path and is authoritative for configured channels.
2. `hybrid`
- Server gate is authoritative and frontend hook provides proactive user guidance.
3. `ui_only`
- Gate executes only in frontend hook layer and does not guarantee non-UI channel blocking.

### 7.2 Channel Coverage Matrix
| Channel | `orm_enforced` | `hybrid` | `ui_only` |
|---|---|---|---|
| Form button click | Enforced | Enforced | Enforced (UI hook) |
| JSON-RPC/XML-RPC direct method call | Enforced | Enforced | Not guaranteed |
| Import/batch scripts | Enforced | Enforced | Not guaranteed |
| Automated actions/server actions | Enforced | Enforced | Not guaranteed |
| Cron/scheduled jobs | Enforced | Enforced | Not guaranteed |

### 7.3 Mode Guardrails
1. `orm_enforced` is recommended default for all new bindings.
2. `ui_only` requires `workflow.binding.risk_ack` with approver identity and reason.
3. `ui_only` shall be rejected when `compliance_tag = compliance_critical`.
4. Mode change from `orm_enforced/hybrid` to `ui_only` requires elevated admin approval and audit event.
5. Mode change from `ui_only` to `orm_enforced/hybrid` is allowed without elevated approval, but prior risk acknowledgment artifact must be archived and `workflow.binding.mode_changed` emitted.

### 7.4 Generic Server Interceptor Contract
1. A central interceptor shall evaluate gate policy for configured `(target_model, target_action_method)` without per-model source edits.
2. Interceptor behavior is configuration-driven from active `workflow.binding` records.
3. In `orm_enforced/hybrid`, interceptor decision is authoritative over frontend state.
4. Interceptor shall emit `workflow.gate.evaluated` audit for allow/block outcomes.
5. Interceptor shall maintain an allow-list of covered invocation paths and record uncovered-path incidents.

### 7.5 Odoo 19 Technical Mechanism
1. Interceptor implementation uses registry-time method patching (`_patch_method`) for configured target methods.
2. Wrapper execution order:
- resolve active binding by request-time context;
- evaluate gate for each target record;
- enforce policy (default batch rule: all-or-nothing block);
- call original method only when gate allows.
3. Wrapper is bound at model class method level, therefore applies consistently to UI, RPC, import scripts, server actions, cron, and `sudo()` invocations.
4. Bypass is allowed only via internal allow-listed flow token created by trusted server code path; client-provided bypass flags are forbidden.
5. Binding enable/disable or target method changes must trigger interceptor map cache refresh.
6. Worker restart/hot-reload constraint:
- interceptor map carries a monotonic `interceptor_config_revision`;
- each worker must refresh map before serving calls on stale revision;
- during refresh window, decision is fail-closed for `orm_enforced/hybrid` and audit records reload state.

### 7.6 Interceptor Safety Rules
1. Client-provided bypass flags are forbidden.
2. Internal bypass tokens may be used only for explicit allow-listed system flows and must be audited.
3. Interceptor failures in `orm_enforced/hybrid` shall fail closed (`blocked`) unless explicit emergency policy permits degraded mode.
4. If target model/module becomes unavailable, binding auto-disables and incident is created.

## 8. Frontend Hook and Gating State Contract
### 8.1 Gating States
1. `blocked`
- Action must not execute; response includes blocking reason and active approval context.
2. `allowed`
- Action can execute immediately.
3. `allowed_with_warning`
- Action can execute but frontend must show warning context from binding policy.

### 8.2 Hook Integration Rules
1. Hook augmentation must preserve native button and form behavior by default.
2. Hook must be additive, not destructive, unless explicitly configured per binding.
3. Hook contract must include state, reason code, and policy message.
4. Hook failure must fail-safe to server truth (interceptor enforcement) in `orm_enforced/hybrid`.

### 8.3 Gate Exception Policy
1. Gate exceptions are optional and must be explicitly enabled per binding.
2. Exception approval requires authorized role and mandatory reason code.
3. Exceptions are disallowed for `compliance_critical` bindings.
4. Each granted exception emits audit event and bounded validity window.

### 8.4 `evaluate_gate` Request/Response Schema
#### Request (`record_context`)
| Field | Type | Required | Description |
|---|---|---|---|
| `model` | `string` | Yes | Target model name (example `sale.order`). |
| `res_ids` | `array<int>` | Yes | Record IDs being executed (one or many). |
| `action_method` | `string` | Yes | Target method (example `action_confirm`). |
| `actor_user_id` | `int` | Yes | Effective user triggering evaluation. |
| `company_id` | `int` | Yes | Request-time company context (not cached session value). |
| `channel` | `string` | Yes | `ui`, `rpc`, `import`, `server_action`, `cron`, `callback`. |
| `request_id` | `string` | No | Correlation reference for observability. |
| `binding_hint_key` | `string` | No | Optional pre-resolved binding key hint. |

#### Response
| Field | Type | Required | Description |
|---|---|---|---|
| `state` | `string` | Yes | `blocked`, `allowed`, `allowed_with_warning`. |
| `reason_code` | `string` | Yes | Deterministic reason (`pending_approval`, `ambiguous_binding`, `invalid_context`, etc.). |
| `policy_message` | `string` | No | User-facing policy message. |
| `binding_id` | `int` | No | Applied binding when resolved. |
| `instance_refs` | `array<object>` | No | Related approval instances by `res_id`. |
| `active_task_ids` | `array<int>` | No | Pending task IDs relevant to the decision. |
| `warning_context` | `object` | No | Warning payload for UI display. |
| `evaluation_ts_utc` | `string` | Yes | ISO timestamp of evaluation. |

## 9. Rollout Scope and Conflict Resolution
### 9.1 Scope Precedence
1. Higher specificity takes precedence: `company > group > global`.
2. Domain scope is evaluated within same specificity level using `binding_priority`.
3. At same specificity, higher `binding_priority` wins.
4. If still tied, configuration is ambiguous.

### 9.2 Ambiguity Handling
1. Ambiguous active bindings at same specificity and priority are blocked at validation/enable time.
2. If ambiguity still occurs at runtime, gate result is `blocked` with `reason_code = ambiguous_binding` and incident creation.
3. Overlap across different specificity levels is allowed and resolved by precedence.

## 10. Withdraw and Forced Reassignment
### 10.1 Requester Withdraw/Cancel (`FR-071`)
1. Request creator may withdraw only while instance is pending and withdraw policy allows it.
2. Withdraw is rejected for terminal states.
3. Terminal approval transition is authoritative; withdraw remains rejected even when callback execution is still running.
4. Withdraw action must capture actor, timestamp, and reason in audit.

### 10.2 Admin Forced Reassignment (`FR-072`)
1. Workflow Admin may reassign pending tasks regardless of original assignee.
2. Reassignment requires reason code and comment.
3. Reassignment must preserve full assignee history and emit audit event.

## 11. Callback Contract
### 11.1 Callback Trigger
1. Callback executes on terminal approval state transition (state-change event), not on repeated button clicks.
2. Callback is optional; if absent, gate release occurs without callback.

### 11.2 Callback Target Definition
1. Canonical target is split fields: `callback_model` and `callback_method`.
2. `callback_target_legacy` (`model.method`) may be accepted at input time only; parser splits at last dot and persists canonical fields.
3. Button methods are supported when callable via model method contract.
4. Example canonical values: `callback_model=sale.order`, `callback_method=action_confirm`.

### 11.3 Callback Validation
1. `callback_model` exists and is installed.
2. `callback_method` exists and is callable.
3. Method signature compatibility is validated against runtime invocation contract.
4. ACL compatibility is validated for configured execution principal.
5. Payload schema compatibility is validated against §11.8.
6. Idempotency policy is configured and compatible with callback semantics.

### 11.4 Callback Execution Principal
1. Execution identity shall be explicitly configured by `callback_execution_principal`.
2. Silent privilege escalation (`sudo` without explicit policy) is forbidden.
3. Cross-company execution must respect company isolation constraints.
4. Callback audit shall include effective execution principal and company context.

### 11.5 Callback Execution and Idempotency
1. Callback execution is effectively-once via idempotency key.
2. Idempotency key must be unique per `(instance_id, binding_id, callback_model, callback_method, terminal_event_id)`.
3. Duplicate callback requests with same key return prior result and do not execute method again.
4. Same key with different payload is rejected with `idempotency_conflict`.

### 11.6 Re-entrancy and Duplicate Effect Protection
1. If callback target equals gated action method, terminal callback execution remains single-effect due to idempotency.
2. Subsequent action invocations after successful callback shall return already-applied outcome or no-op response.
3. Retry after response-loss shall not create duplicate business side effects.
4. Cross-binding callback recursion shall be limited by max callback depth; depth overflow creates incident and stops chain.

### 11.7 Callback Failure and Recovery
1. Failure creates `workflow.incident` with failure category and technical context.
2. Failure does not erase approval evidence or audit trail.
3. Controlled retry action is allowed by authorized roles with idempotency safeguards.
4. Recovery action options include `retry`, `skip_with_approval`, and `manual_resolution_link` per policy.

### 11.8 Callback Payload Schema (Minimum Contract)
| Field | Type | Required | Description |
|---|---|---|---|
| `instance_id` | `int` | Yes | Workflow instance identifier. |
| `binding_id` | `int` | Yes | Binding used to trigger callback. |
| `terminal_event_id` | `string` | Yes | Terminal transition event reference. |
| `target_model` | `string` | Yes | Business model of record being approved. |
| `target_res_id` | `int` | Yes | Business record ID. |
| `decision` | `string` | Yes | `approved` or `rejected`. |
| `effective_actor_user_id` | `int` | Yes | Effective execution principal user ID. |
| `approved_at_utc` | `string` | Yes | ISO timestamp of terminal approval. |
| `idempotency_key` | `string` | Yes | Callback idempotency key. |
| `correlation_id` | `string` | Yes | Correlation identifier for tracing. |
| `causation_id` | `string` | No | Parent operation reference. |
| `extra_payload` | `object` | No | Optional extension payload under schema governance in `SRS-10`. |

`extra_payload` must pass schema-registry validation (versioned contract from `SRS-10`) before callback execution is allowed.

## 12. APIs and Events (Binding Lifecycle)
### 12.1 Logical Operations
1. `create_binding(payload)`
2. `update_binding(binding_id, payload, expected_revision)`
3. `validate_binding(binding_id)`
4. `enable_binding(binding_id)`
5. `disable_binding(binding_id)`
6. `evaluate_gate(record_context)`
7. `grant_gate_exception(instance_id, actor, reason_code, valid_until_utc)`
8. `withdraw_request(instance_id, actor, reason_code)`
9. `force_reassign(task_id, new_assignee, actor, reason_code)`
10. `execute_callback(instance_id, callback_model, callback_method, payload, idempotency_key)`
11. `retry_callback(incident_id, actor, idempotency_key)`

### 12.2 Required Audit Events
1. `workflow.binding.created`
2. `workflow.binding.updated`
3. `workflow.binding.enabled`
4. `workflow.binding.disabled`
5. `workflow.binding.mode_changed`
6. `workflow.binding.risk_acknowledged`
7. `workflow.gate.evaluated`
8. `workflow.gate.exception_granted`
9. `workflow.interceptor.path_uncovered`
10. `workflow.request.withdrawn`
11. `workflow.task.force_reassigned`
12. `workflow.callback.validated`
13. `workflow.callback.executed`
14. `workflow.callback.failed`
15. `workflow.callback.retried`

## 13. Acceptance Criteria and Test Scenarios
| Test ID | Requirement IDs | Scenario | Expected Result |
|---|---|---|---|
| `TC-FR-007-001` | `FR-007` | Create binding for `sale.order.action_confirm` to definition key | Binding saved and linked to definition key |
| `TC-FR-008-001` | `FR-008` | Execute bound action with pending approvals | Action blocked with gating reason |
| `TC-FR-008-002` | `FR-008` | Execute bound action after terminal approval | Action allowed |
| `TC-FR-008-003` | `FR-008` | Request gate exception without policy enabled | Request rejected |
| `TC-FR-008-004` | `FR-008` | Request gate exception on `compliance_critical` binding | Request rejected |
| `TC-FR-009-001` | `FR-009` | Load bound form view with JS hook | Hook receives gating payload and renders state |
| `TC-FR-010-001` | `FR-010`, `NFR-011` | Enable hook on existing form | Native form elements remain intact by default |
| `TC-FR-011-001` | `FR-011` | Configure company and global bindings for same action | Company binding takes precedence |
| `TC-FR-011-002` | `FR-011` | Two same-specificity bindings with same priority | Validation blocks ambiguous configuration |
| `TC-FR-011-003` | `FR-011` | Save domain scope with unknown field in domain payload | Validation rejected with deterministic error |
| `TC-FR-012-001` | `FR-012` | Disable binding | Binding stops gating new actions; history remains |
| `TC-FR-012-002` | `FR-012` | Disable binding while instance pending | Existing instance proceeds; new starts ignore binding |
| `TC-FR-012-003` | `FR-012` | Target model module removed after binding was enabled | Binding auto-disabled and incident created |
| `TC-FR-071-001` | `FR-071` | Request creator withdraws pending instance under allowed policy | Instance withdrawn and audit captured |
| `TC-FR-071-002` | `FR-071` | Request creator withdraws terminal instance | Operation rejected with policy reason |
| `TC-FR-071-003` | `FR-071` | Request creator attempts withdraw while callback is running after terminal transition | Operation rejected |
| `TC-FR-072-001` | `FR-072` | Workflow Admin force reassigns pending task | Task reassigned with reason and full audit |
| `TC-FR-072-002` | `FR-072` | Withdraw and force-reassign race on same task | Deterministic conflict handling |
| `TC-FR-081-001` | `FR-081` | Gate evaluation on pending instance | Hook state is `blocked` |
| `TC-FR-081-002` | `FR-081` | Gate evaluation on clear path | Hook state is `allowed` |
| `TC-FR-081-003` | `FR-081` | Gate evaluation with warning policy | Hook state is `allowed_with_warning` |
| `TC-FR-081-004` | `FR-081` | Gate evaluation context missing required scope fields | Fail-safe `blocked` with `invalid_context` |
| `TC-FR-081-005` | `FR-081` | `evaluate_gate` response contract validation | Response includes required schema fields |
| `TC-FR-081-006` | `FR-081` | Concurrent final approval commit and gate evaluation race | Deterministic read-committed behavior with retry-safe decision outcome |
| `TC-FR-090-001` | `FR-090` | Create binding in each enforcement mode | All modes accepted under policy constraints |
| `TC-FR-090-002` | `FR-090` | Change mode from `ui_only` to `orm_enforced` | Transition succeeds, risk-ack archived, audit emitted |
| `TC-FR-091-001` | `FR-091`, `NFR-017` | Invoke action through RPC in `orm_enforced` mode | Gate enforcement matches UI behavior |
| `TC-FR-091-002` | `FR-091`, `NFR-017` | Invoke action via cron/server action in `hybrid` mode | Gate enforcement applies consistently |
| `TC-FR-091-003` | `FR-091`, `NFR-017` | Enforce configured method without per-model custom code | Interceptor blocks/permits correctly from central config |
| `TC-FR-091-004` | `FR-091`, `NFR-017` | Invoke method through `sudo()` context | Interceptor still enforces gate policy |
| `TC-FR-091-005` | `FR-091`, `NFR-017` | Multi-record action on mixed approval states | Default all-or-nothing blocking enforced |
| `TC-FR-092-001` | `FR-092` | Configure `ui_only` without risk acknowledgment | Validation rejected |
| `TC-FR-092-002` | `FR-092` | Configure `ui_only` on `compliance_critical` binding | Validation rejected |
| `TC-FR-092-003` | `FR-092` | Execute import path under `ui_only` mode | Behavior documented as not guaranteed; warning/audit emitted |
| `TC-FR-093-001` | `FR-093` | Configure callback canonical fields | Callback target stored and bound |
| `TC-FR-093-002` | `FR-093` | Callback target equals gated action method | Single business effect under terminal callback + idempotency |
| `TC-FR-093-003` | `FR-093` | Configure callback via legacy `model.method` input | Value normalized to canonical fields |
| `TC-FR-094-001` | `FR-094` | Enable binding with missing callback method | Validation blocked with callable-not-found |
| `TC-FR-094-002` | `FR-094` | Enable binding with ACL-incompatible callback principal | Validation blocked with ACL error |
| `TC-FR-094-003` | `FR-094` | Enable binding with incompatible callback signature | Validation blocked with signature error |
| `TC-FR-094-004` | `FR-094` | Enable binding with invalid callback payload contract | Validation blocked with payload schema error |
| `TC-FR-095-001` | `FR-095` | Callback execution raises runtime exception | Incident created; audit preserved; retry control exposed |
| `TC-FR-095-002` | `FR-095` | Retry callback after temporary failure | Callback succeeds and incident resolved |
| `TC-FR-095-003` | `FR-095` | Callback succeeds but response lost then retry occurs | Prior success returned; no duplicate side effect |
| `TC-FR-095-004` | `FR-095` | Callback method removed after binding enable | Incident created; retry blocked until binding fixed |
| `TC-FR-095-005` | `FR-095` | Circular callback chain depth exceeded | Incident created and recursion stopped |
| `TC-NFR-011-001` | `NFR-011` | Regression check of hook on baseline modules (`sale`, `purchase`, `hr_holidays`) | No regressions in supported interactions |
| `TC-NFR-017-001` | `NFR-017` | Compare gate results across UI and non-UI for same record in `orm_enforced` mode | Results are consistent |
| `TC-NFR-017-002` | `NFR-017` | Frontend hook fails in `hybrid` mode | Server interceptor remains authoritative |

## 14. Traceability Matrix
| Canonical ID | Covered Sections | Primary Tests |
|---|---|---|
| `FR-007` | 4, 6, 12 | `TC-FR-007-001` |
| `FR-008` | 4, 8, 12 | `TC-FR-008-001`, `TC-FR-008-002`, `TC-FR-008-003`, `TC-FR-008-004` |
| `FR-009` | 4, 8 | `TC-FR-009-001` |
| `FR-010` | 4, 8 | `TC-FR-010-001` |
| `FR-011` | 4, 6, 9 | `TC-FR-011-001`, `TC-FR-011-002`, `TC-FR-011-003` |
| `FR-012` | 4, 6 | `TC-FR-012-001`, `TC-FR-012-002`, `TC-FR-012-003` |
| `FR-071` | 4, 10 | `TC-FR-071-001`, `TC-FR-071-002`, `TC-FR-071-003` |
| `FR-072` | 4, 10 | `TC-FR-072-001`, `TC-FR-072-002` |
| `FR-081` | 4, 8, 12 | `TC-FR-081-001`, `TC-FR-081-002`, `TC-FR-081-003`, `TC-FR-081-004`, `TC-FR-081-005`, `TC-FR-081-006` |
| `FR-090` | 4, 7 | `TC-FR-090-001`, `TC-FR-090-002` |
| `FR-091` | 4, 7 | `TC-FR-091-001`, `TC-FR-091-002`, `TC-FR-091-003`, `TC-FR-091-004`, `TC-FR-091-005` |
| `FR-092` | 4, 7 | `TC-FR-092-001`, `TC-FR-092-002`, `TC-FR-092-003` |
| `FR-093` | 4, 11 | `TC-FR-093-001`, `TC-FR-093-002`, `TC-FR-093-003` |
| `FR-094` | 4, 11 | `TC-FR-094-001`, `TC-FR-094-002`, `TC-FR-094-003`, `TC-FR-094-004` |
| `FR-095` | 4, 11 | `TC-FR-095-001`, `TC-FR-095-002`, `TC-FR-095-003`, `TC-FR-095-004`, `TC-FR-095-005` |
| `NFR-011` | 4, 8 | `TC-FR-010-001`, `TC-NFR-011-001` |
| `NFR-017` | 4, 7 | `TC-FR-091-001`, `TC-FR-091-002`, `TC-FR-091-003`, `TC-FR-091-004`, `TC-FR-091-005`, `TC-NFR-017-001`, `TC-NFR-017-002` |

## 15. Edge Case Register
| Edge Case ID | Edge Case | Expected Behavior | Owner | Linked Test ID |
|---|---|---|---|---|
| `EC-02-01` | Multiple active bindings at same specificity and priority for same model/action | Block enable and require disambiguation | Tech Lead | `TC-FR-011-002` |
| `EC-02-02` | Binding disabled while instance pending | Existing instance lifecycle continues; new gate checks ignore disabled binding | Workflow Admin | `TC-FR-012-002` |
| `EC-02-03` | `ui_only` binding used by import script | Non-UI execution not guaranteed blocked; warning and audit record required | Tech Lead | `TC-FR-092-003` |
| `EC-02-04` | Frontend hook unavailable due to JS error in `hybrid` mode | Server-side interceptor remains authoritative | Tech Lead | `TC-NFR-017-002` |
| `EC-02-05` | Callback succeeds but response lost (retry occurs) | Idempotency returns prior success without duplicate business effect | Integration Lead | `TC-FR-095-003` |
| `EC-02-06` | Callback target method removed after binding enabled | Runtime failure creates incident; retry blocked until binding fixed | Workflow Admin | `TC-FR-095-004` |
| `EC-02-07` | Requester withdraw and admin reassign race on same task | Deterministic conflict handling; one operation wins and loser gets conflict | Tech Lead | `TC-FR-072-002` |
| `EC-02-08` | Gate evaluation context lacks required scope fields | Default fail-safe `blocked` with `reason_code = invalid_context` | Tech Lead | `TC-FR-081-004` |
| `EC-02-09` | Multi-record invocation where subset has pending approvals | Default all-or-nothing block for the batch | Tech Lead | `TC-FR-091-005` |
| `EC-02-10` | Callback chain recursion across bindings | Max depth protection triggers incident and halts recursion | Integration Lead | `TC-FR-095-005` |
| `EC-02-11` | Target model uninstalled after binding creation | Auto-disable binding and create incident | Workflow Admin | `TC-FR-012-003` |
| `EC-02-12` | Concurrent final approval and gate read in separate transactions | Decision uses committed state; stale reads require deterministic retry path | Tech Lead | `TC-FR-081-006` |
| `EC-02-13` | Company switched in multi-company session | Gate uses request-time company context only | Tech Lead | `TC-FR-081-005` |
| `EC-02-14` | Referenced definition key archived while binding remains enabled | Enable/validation rejects unresolved definition key and raises incident | Workflow Admin | `TC-FR-007-001` |

## 16. Sign-off Checklist
1. All inherited requirements listed in Section 3 are mapped in Section 14.
2. Every mapped requirement has at least one acceptance test in Section 13.
3. Enforcement mode semantics are consistent with channel coverage table.
4. Generic server interceptor contract is explicit and testable without per-model source edits.
5. `ui_only` risk controls and compliance restrictions are explicit.
6. Callback principal, payload schema, idempotency, and duplicate-effect protections are defined.
7. Cross-SRS boundaries with `SRS-01`, `SRS-04`, `SRS-05`, `SRS-07`, and `SRS-10` are consistent.

## 17. Open Issues
1. Full invocation-path coverage matrix and residual uncovered path list require implementation POC evidence.
2. Policy defaults for `skip_with_approval` callback recovery need compliance sign-off.
3. Extension fields inside `extra_payload` must follow `SRS-10` schema governance process.

## 18. Next Document
After approval of `SRS-02`, proceed to `srs_05_approver_resolution_human_tasks.md`.
