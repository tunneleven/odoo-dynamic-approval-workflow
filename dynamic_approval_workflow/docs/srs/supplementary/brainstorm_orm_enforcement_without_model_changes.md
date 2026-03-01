# Brainstorm Report: Enforcing Approval Without Per-Model Source Changes

Version: `v1.0-draft`
Date: `2026-02-27`
Context: Dynamic Approval Workflow (`SRS-02` scope)

## 1. Objective
Find practical ways to enforce approval gating in Odoo while avoiding per-model source code edits, with user preference toward `ui_only` behavior where possible.

## 2. Problem Statement
In Odoo, pure UI enforcement is not equivalent to ORM enforcement.

If enforcement exists only in form-view JS hooks:
1. UI button clicks can be blocked.
2. Non-UI channels can still invoke the same business method:
- RPC/API calls
- imports and scripts
- server actions
- cron jobs
- automation flows

So the design problem is: how to keep low implementation effort while controlling bypass risk.

## 3. Decision Constraints
1. Avoid editing source code for each business model (`sale.order`, `purchase.order`, etc.).
2. Keep configuration-driven behavior in admin UI.
3. Support optional `ui_only` mode for simple models.
4. Maintain a path for stronger controls on critical/compliance models.
5. Keep Odoo upgrades manageable.

## 4. Options Considered

### Option A: Pure UI-Only
Description:
1. Enforce in JS hook only.
2. Do not add server-side gate interceptor.

Pros:
1. Fastest to ship.
2. No invasive backend interception.
3. Lowest maintenance cost initially.

Cons:
1. High bypass risk via non-UI channels.
2. Not suitable for compliance-critical actions.
3. Hard to defend in audits if business says "approval is mandatory."

Best fit:
1. Low-risk/simple models.
2. Internal teams with strong process discipline.

---

### Option B: Generic Server Interceptor (No Per-Model Edits)
Description:
1. Build one central addon that intercepts method execution for configured `(model, method)`.
2. Keep configuration in `workflow.binding`.
3. Do not edit each target model file.

Implementation patterns:
1. `call_kw` interception: evaluate gate for external method invocations.
2. Dynamic runtime method wrapping by registry load for configured methods.

Pros:
1. Near-ORM protection without per-model modifications.
2. Consistent behavior across UI/RPC/import/cron (depending on interception depth).
3. Stronger audit/compliance posture.

Cons:
1. More complex than UI-only.
2. Needs careful compatibility testing on Odoo upgrades.
3. Risk of false positives if context handling is not well designed.

Best fit:
1. Medium/high-risk models.
2. Teams wanting strong enforcement but low model-specific code churn.

---

### Option C: Hybrid Risk-Tier Strategy (Recommended)
Description:
1. Keep `ui_only` allowed for low-risk models with explicit risk acknowledgment.
2. Use generic server interceptor for medium/high-risk models.
3. For compliance-critical bindings, disallow `ui_only`.

Pros:
1. Matches your preference while protecting critical paths.
2. Reduces implementation pressure versus full strict ORM everywhere.
3. Clear governance model for auditors and operations.

Cons:
1. Requires risk classification policy.
2. Slightly more governance complexity.

Best fit:
1. Real enterprise deployments with mixed process criticality.

## 5. Comparative Scorecard
Scoring: 1 (weak) to 5 (strong)

| Criteria | Option A UI-only | Option B Generic Interceptor | Option C Hybrid Risk-Tier |
|---|---:|---:|---:|
| Delivery speed | 5 | 3 | 4 |
| Non-UI protection | 1 | 4 | 4 |
| Compliance readiness | 1 | 4 | 5 |
| Upgrade resilience | 4 | 3 | 3 |
| Operational simplicity | 4 | 3 | 3 |
| Long-term risk control | 1 | 4 | 5 |
| Overall balance | 2 | 4 | 5 |

## 6. Recommended Target Architecture (Option C)

### 6.1 Policy Layer
Define binding risk tiers:
1. `low_risk`
- `ui_only` allowed with risk acknowledgment.
2. `standard_risk`
- `hybrid` recommended.
3. `compliance_critical`
- `orm_enforced` mandatory.

### 6.2 Enforcement Layer
1. UI hook always evaluates gate for user guidance.
2. Server interceptor evaluates gate for configured bindings requiring server protection.
3. Response states: `blocked`, `allowed`, `allowed_with_warning`.

### 6.3 Callback Layer
1. Terminal approval triggers callback once (effectively-once via idempotency key).
2. Callback failures create incidents and controlled retries.
3. Callback execution identity must be explicit and auditable.

### 6.4 Governance Layer
1. `ui_only` requires risk acknowledgment record.
2. Compliance-critical + `ui_only` rejected at validation time.
3. Mode changes create audit events and require elevated approval.

## 7. Detailed Design Notes for "No Per-Model Edits"

### 7.1 Practical Interception Choices
1. Central `call_kw` interception:
- Good coverage for RPC-like calls.
- May miss some internal method-to-method calls.

2. Dynamic method wrapping from binding config:
- Better coverage for direct method invocation paths.
- More careful engineering needed to avoid side effects.

Pragmatic sequence:
1. Phase 1: `call_kw` interception + UI hook.
2. Phase 2: add selective method wrapping for high-risk models.

### 7.2 Safe Bypass Mechanism
A bypass is needed for controlled internal operations (for example callback recursion prevention), but must be strict.

Rules:
1. No open bypass context key accepted from client.
2. Bypass token generated server-side only.
3. Bypass always audited with reason and actor/system principal.
4. Bypass allowed only for explicit allow-listed operations.

### 7.3 Performance Guardrails
1. Cache binding lookup by `(model, method, company)`.
2. Short-circuit gate evaluation when no active binding exists.
3. Track P95 gate check latency and incident on degradation.

## 8. If You Still Choose Mostly UI-Only
Use compensating controls to reduce risk:
1. Restrict external API access for affected models.
2. Disable direct import for gated actions where possible.
3. Block critical server actions/cron on those models.
4. Add anomaly report: detect state changes that occurred without approval instance.
5. Monthly audit report for suspected bypass events.

This does not eliminate bypass risk, but it can make risk visible and manageable for low-risk domains.

## 9. Legal/Compliance Interpretation
1. If policy language says approval is mandatory, pure `ui_only` is weak because enforcement is channel-dependent.
2. Hybrid policy with documented risk-tier and explicit exceptions is generally more defensible.
3. Compliance-critical processes should have server-side enforcement and immutable audit traces.

## 10. Implementation Phasing Proposal

### Phase 1 (Fast)
1. Ship UI hook gating + risk-tier policy + `ui_only` acknowledgment.
2. Enforce `ui_only` prohibition for compliance-critical bindings.
3. Add callback idempotency and incident controls.

### Phase 2 (Control)
1. Add generic server interceptor for `orm_enforced/hybrid` bindings.
2. Add channel consistency tests (UI/RPC/import/cron).
3. Add callback execution principal contract.

### Phase 3 (Hardening)
1. Add selective deeper method wrapping for critical methods.
2. Add bypass anomaly detector and operational dashboards.
3. Add upgrade test suite for interceptor compatibility.

## 11. Recommended SRS-02 Updates
1. Add a dedicated section: `Execution Principal and Privilege Boundary` for callbacks.
2. Add explicit `Gate Exception Policy` contract.
3. Add deterministic behavior when callback target equals gated action method.
4. Promote planned edge-case tests into acceptance table.
5. Add risk-tier decision table mapping to enforcement modes.

## 12. Final Recommendation
Use Option C (Hybrid Risk-Tier):
1. Honor business preference by allowing `ui_only` for simple low-risk models.
2. Protect critical/compliance flows with server-side generic enforcement without per-model edits.
3. Keep rollout incremental to reduce delivery risk.

This gives the best balance between speed, maintainability, and enforcement credibility.
