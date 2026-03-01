# SRS-05 Review Report: Approver Resolution and Human Tasks

**Reviewer:** AI Spec Reviewer
**Date:** 2026-02-28
**Review Iteration:** 1 (against `v1.1-draft`)
**Document Under Review:** `srs_05_approver_resolution_human_tasks.md` (`v1.1-draft`, 2026-02-28)
**Baseline References:** `dynamic_approval_workflow_srs_v1.3.md`, `srs_00_master_traceability.md`

---

## Executive Summary

**Overall Assessment: CONDITIONALLY READY — Core resolution and task lifecycle can start; important specification gaps remain**

SRS-05 covers all 20 canonical IDs (`FR-029..042`, `FR-047..050`, `FR-074`, `NFR-014`) with 17 DFRs, complete traceability, and a well-structured task lifecycle. The approver resolution contract, delegation rules, anti-self/SoD policies, and batch action contract are solid.

However, there are **0 Critical**, **5 Important**, and **6 Minor** gaps. The most significant issues are: (1) quorum semantics overlap/conflict with SRS-04, (2) API input/output contracts are undefined, (3) edge-case tests remain "(planned)" outside the acceptance table, (4) escalation target resolution and chain depth are under-specified, and (5) `record_field_ref` resolution contract lacks detail.

---

## 1. Requirement Coverage Verification

### 1.1 Canonical Mapping (PASS)

All assigned canonical IDs from SRS-00 §7 for SRS-05 are present in:
1. Section 3 — inherited scope
2. Section 4 — DFR table (17 DFRs mapping to 20 canonical IDs)
3. Section 14 — traceability matrix (20 entries)

No orphan DFR detected. No missing canonical ID.

### 1.2 Coverage Depth Assessment

| Canonical ID | Depth |
|---|---|
| `FR-029` | Adequate — named user resolution |
| `FR-030` | Adequate — group/role expansion |
| `FR-031` | **Partial** — hierarchy resolution stated but chain traversal rules under-specified |
| `FR-032` | **Shallow** — field reference resolution lacks type/validation rules |
| `FR-033` | Good — delegation with validity and audit |
| `FR-034` | Good — anti-self policy |
| `FR-035` | Good — SoD policy |
| `FR-036` | **Partial** — quorum stated but overlaps with SRS-04 §8 without clear boundary |
| `FR-037` | Adequate — task creation |
| `FR-038` | Adequate — action set defined |
| `FR-039` | Adequate — SLA deadline |
| `FR-040` | **Partial** — escalation rules stated but target resolution under-specified |
| `FR-041` | Adequate — reminder scheduling |
| `FR-042` | Good — immutable history |
| `FR-047..050` | Adequate — follower policies |
| `FR-074` | Good — batch with partial success |
| `NFR-014` | Adequate — mobile baseline defined |

### 1.3 Cross-SRS Boundary References

| Boundary | Referenced? | Assessment |
|---|---|---|
| SRS-03 (diagram/viewer) | Yes, in Scope | OK |
| SRS-04 (runtime orchestration) | Yes, in Scope | **Overlap** — quorum semantics defined in both SRS-04 §8 and SRS-05 §6/§8. Ownership boundary unclear. |
| SRS-06 (signature evidence) | Yes, in Scope | OK — defers signature semantics |
| SRS-07 (access/security) | Referenced in §16 checklist | **Partial** — temporary access grant lifecycle (SRS-07 §7) is tightly coupled to task creation/completion but no explicit cross-reference in SRS-05 body |
| SRS-08 (notifications) | Not referenced | **Missing** — reminders and escalation notifications are implemented via SRS-08 notification engine, but SRS-05 doesn't reference or coordinate |
| SRS-10 (data model) | Not referenced | **Missing** — task and resolution data models should cross-reference SRS-10 |

---

## 2. Findings (Ordered by Severity)

### 2.1 Important Findings

| ID | Location | Finding | Impact | Recommendation |
|---|---|---|---|---|
| GAP-05-01 | §6 (DFR-05-008), §8.3 vs SRS-04 §8 | **Quorum semantics dual-ownership.** SRS-05 §6/§8 defines "minimum approver counts and quorum thresholds" per step (DFR-05-008, FR-036). SRS-04 §8 defines quorum computation (absolute/percentage/floor), eligible set snapshot, and outcome resolution (FR-024, FR-082). The boundary between SRS-04's quorum (token/join-level) and SRS-05's quorum (task/step-level) is not explicitly drawn. Does SRS-05 define the policy configuration and SRS-04 the runtime evaluation? Or does SRS-05 independently evaluate quorum? `TC-FR-036-001` tests "completion follows quorum/min policy" but the evaluating component is ambiguous. | Developers may implement quorum logic in two places, causing inconsistent behavior or double-counting. | Add explicit boundary statement: SRS-05 owns quorum *configuration and policy definition* per step; SRS-04 owns quorum *runtime evaluation and outcome resolution*. SRS-05 task completion signals feed SRS-04 quorum counter. Add cross-reference to SRS-04 §8. |
| GAP-05-02 | §12.1 | **API operation input/output contracts undefined.** 9 logical operations listed but no request/response schemas. Key gaps: (a) `resolve_approvers` — what does it return? User IDs? Actor objects with source type and priority? (b) `perform_task_action` — what is in `payload`? Comment? Signature data? Condition evidence? (c) `batch_task_action` — response shape for partial success not structurally defined beyond prose in §9. | Frontend/backend developers cannot implement without guessing payload shapes. Batch result parsing will diverge. | Define request/response schemas for at least `resolve_approvers`, `perform_task_action`, and `batch_task_action`. For batch, define explicit JSON structure: `{total, succeeded, failed, results: [{task_id, status, error_code?, message?}]}`. |
| GAP-05-03 | §15 | **4 edge-case tests remain "(planned)" outside §13 acceptance table.** `TC-FR-030-002`, `TC-FR-035-002`, `TC-FR-033-003`, `TC-FR-074-002` are in edge case register but not promoted. Per SRS-00 §8.2, compliance/security requirements must have negative-path tests. `TC-FR-035-002` (all approvers filtered by SoD) is a security negative-path test that should be mandatory. | Traceability appears complete but actual test baseline is weaker than implied. SRS-00 sign-off criteria may not be met. | Promote all 4 planned tests into §13 acceptance table. At minimum, `TC-FR-035-002` and `TC-FR-033-003` must be mandatory before sign-off. |
| GAP-05-04 | §8.3 | **Escalation target resolution undefined.** §8.3 says "escalation targets are resolved through same identity validation rules" but doesn't specify: (a) who is the escalation target — next-level manager? A configured fallback user/group? (b) maximum escalation chain depth, (c) behavior when escalation target is the same as original assignee, (d) behavior when escalation target cannot be resolved. | Developers cannot implement escalation without guessing the target resolution strategy. Unbounded escalation chains risk infinite loops. | Add escalation target resolution contract: source type (configured escalation target per step, manager-chain, fallback group), maximum chain depth, same-actor guard, and empty-target incident behavior. |
| GAP-05-05 | §6.1, §6.4 | **`record_field_ref` resolution contract under-specified.** §6.1 lists `record_field_ref` as a source type and §6.4 applies policy constraints, but the actual field resolution rules are missing: (a) what field types are supported (Many2one to res.users? Many2many? Related fields? Computed fields?), (b) multi-value field handling (Many2many resolves to multiple approvers?), (c) empty field handling (null/False — fallback or incident?), (d) field access validation (can the field be read by the resolution engine?). | Implementation will vary: one developer may support only Many2one, another may support computed fields, leading to inconsistent behavior across deployments. | Add field reference resolution rules: supported field types, multi-value expansion semantics, null handling (fallback policy or incident), and field readability validation at binding/publish time. |

### 2.2 Minor Findings

| ID | Location | Finding | Impact | Recommendation |
|---|---|---|---|---|
| GAP-05-06 | §7.1 | **Delegation chain depth unstated.** §7.1 defines delegation with validity window but doesn't address: can delegate A further delegate to B? If yes, what is the maximum chain depth? If no, is re-delegation explicitly blocked? | Unbounded delegation chains or unexpected blocking of legitimate re-delegation. | State explicitly: single-level delegation only (re-delegation blocked) or configurable max depth with audit trail for chain. |
| GAP-05-07 | §8.1 | **Task state transition matrix missing.** 8 task states are listed but no state transition matrix defines which transitions are valid. E.g., can a task go from `escalated` to `approved`? From `delegated` to `rejected`? From `changes_requested` to `approved`? | Developers must infer valid transitions; invalid transitions may be allowed or valid ones blocked. | Add a state transition matrix: rows = current state, columns = action, cells = target state or "invalid". |
| GAP-05-08 | §8.2, §8.4 | **`request_changes` lifecycle incomplete.** §8.2 lists `request_changes` as an action and §8.1 has `changes_requested` state, but the lifecycle after changes are requested is undefined: who acts next? Does the requester resubmit? Does the task auto-return to the same approver? Is a new task created? | Developers cannot implement the request-changes flow end-to-end. | Define the changes-requested lifecycle: requester notification, resubmission mechanism (new task or task reactivation), and whether the same or different approver reviews the updated record. Cross-reference SRS-04 rework loop contract if applicable. |
| GAP-05-09 | §11 | **Mobile baseline too narrow.** §11 defines one viewport (390x844) and touch-only. No landscape mode, no tablet profile, no minimum OS/browser version. `NFR-014` says "mobile form factors" (plural). | QA scope is incomplete; users on tablets or landscape phones may have degraded experience. | Add at minimum: tablet baseline (768x1024), landscape constraint (layout must not break), and minimum browser baseline (last 2 versions of Safari/Chrome mobile). |
| GAP-05-10 | §7.2 | **Anti-self removal vs blocking behavior ambiguous.** §7.2 says "requester must be removed or blocked per policy" — these are two different behaviors with different user experiences. Removal silently excludes the requester; blocking halts the entire step. Which is default? Is this configurable? | Inconsistent default behavior across implementations. | Define default (removal with logging) and configurable alternative (hard block with incident). |
| GAP-05-11 | §10 | **Follower integration with Odoo `mail.followers` unspecified.** SRS-05 defines custom follower subscription objects but Odoo has a native follower/subscriber system (`mail.thread`, `mail.followers`). The relationship between `workflow.follower_subscription` and Odoo's native follower system is undefined. | Dual follower systems: workflow-specific and Odoo-native, causing notification duplication or missed notifications. | Clarify whether workflow followers are implemented via Odoo's native `mail.followers` mechanism or a parallel custom system, and how duplicates are prevented. |

---

## 3. Edge Case Coverage Assessment

### 3.1 Covered Edge Cases

| EC ID | Edge Case | Test Coverage |
|---|---|---|
| EC-05-01 | Duplicate approver from multiple sources | `TC-FR-030-002` (planned — not in §13) |
| EC-05-02 | All approvers filtered by anti-self/SoD | `TC-FR-035-002` (planned — not in §13) |
| EC-05-03 | Delegate becomes inactive during validity | `TC-FR-033-003` (planned — not in §13) |
| EC-05-04 | Batch includes terminal tasks | `TC-FR-074-002` (planned — not in §13) |

### 3.2 Missing Edge Cases

| ID | Missing Edge Case | Risk | Recommendation |
|---|---|---|---|
| EC-M1 | **Approver resolved from group where group membership changes after task creation.** User removed from group while task is pending. | Task assigned to user who no longer qualifies; action may succeed or fail depending on recheck timing. | Define policy: task persists with original assignment (snapshot) or real-time membership recheck on action. |
| EC-M2 | **Hierarchy resolution with no manager configured.** `requester_hierarchy` source with employee who has no parent/manager in HR. | Resolution returns empty set; if no fallback, incident. But no test exists. | Add test and define explicit behavior: fallback to configured default or incident with actionable message. |
| EC-M3 | **SoD conflict created by delegation.** Original approver A can act (no SoD conflict). A delegates to B. B has SoD conflict with prior step approver. | Delegation succeeds but delegated action is blocked by SoD — poor UX and wasted time. | Define SoD pre-check at delegation time: block delegation if delegate would violate SoD. |
| EC-M4 | **Concurrent task actions from same approver.** Approver clicks "approve" twice rapidly (double-submit) or in two browser tabs. | Duplicate task transitions; second action on already-approved task. | Define idempotent task action behavior: second identical action returns prior result. Cross-reference SRS-10 idempotency contract. |
| EC-M5 | **Quorum met by timeout auto-decisions only.** All approvers time out; auto-approve fills quorum. No human actually approved. | Technically valid per spec but may violate business intent for certain compliance-critical workflows. | Define policy flag: `require_human_quorum_contribution` that blocks pure-timeout quorum satisfaction when compliance-critical. Cross-reference SRS-04 §9 timeout auto-decision. |
| EC-M6 | **Batch action across multiple companies.** Tasks from different companies in single batch request. Company isolation must be enforced per-record. | Cross-company approval if isolation check is only at batch level, not per-record. | State that batch permission check includes company isolation per-record. Cross-reference SRS-07 §8 isolation. |
| EC-M7 | **Reminder/escalation fires after task already completed.** Cron job evaluates SLA after task was just approved in a concurrent transaction. | Spurious reminder/escalation notification for already-completed task. | Define guard: reminder/escalation must verify task is still pending before dispatching. Add test. |
| EC-M8 | **`request_changes` action followed by new approval cycle but original SLA has expired.** SLA was computed at initial task creation; after changes, does a new SLA window start? | Approver receives changes but task is already "overdue" from original SLA — misleading and may auto-escalate immediately. | Define SLA reset policy for resubmitted/reactivated tasks after `request_changes`. |
| EC-M9 | **Follower policy removes requester as follower before instance completes.** Completion downgrade policy runs early due to partial step completion. | Requester loses visibility into their own approval request. | Define guard: requester cannot be removed as follower while instance is non-terminal, regardless of step-level policy. |
| EC-M10 | **Delegation to user in different company.** Delegator in Company A delegates to user in Company B. | Cross-company task action; violation of company isolation. | Block cross-company delegation with explicit error. Cross-reference SRS-07 isolation rules. |

---

## 4. Cross-SRS Boundary Assessment

| Boundary | Status | Detail |
|---|---|---|
| **SRS-05 ↔ SRS-04** | **Overlap risk** | Quorum semantics (FR-036 in SRS-05, FR-024/FR-082 in SRS-04) are defined in both documents without explicit ownership boundary. SRS-04 §8 is more detailed (computation, snapshot, outcome resolution). SRS-05 should defer quorum evaluation to SRS-04 and own only the policy configuration. |
| **SRS-05 ↔ SRS-06** | OK | Correctly defers signature evidence. SRS-06 references `task_id` and task actions for signature capture. |
| **SRS-05 ↔ SRS-07** | **Partial** | Temporary access grants (SRS-07 DFR-07-001) are triggered by task creation and revoked on task completion. SRS-05 doesn't reference this lifecycle dependency. Task creation should trigger access provisioning; task terminal transition should trigger revocation. |
| **SRS-05 ↔ SRS-08** | **Missing** | SRS-08 owns notification delivery for assignment, reminders, escalation, and outcomes (DFR-08-001). SRS-05 §8.3 defines reminder and escalation scheduling but doesn't reference SRS-08 as the delivery mechanism. The handoff (SRS-05 emits event → SRS-08 delivers notification) is not formalized. |
| **SRS-05 ↔ SRS-10** | **Not referenced** | Task data model, resolution rule schema, and transition event structure should cross-reference SRS-10. |

---

## 5. Strengths

1. **Comprehensive resolution source types** (§6) — four source types covering all common enterprise approver patterns with clear de-duplication and exclusion rules.
2. **Strong policy constraint model** (§6.4, §7) — anti-self, SoD, and delegation controls run after resolution and before task creation, preventing policy-violating tasks from ever being created.
3. **Good batch action contract** (§9) — per-record permission checks with partial-success reporting is a well-designed pattern for enterprise batch operations.
4. **Immutable task history** (§8.4) — every transition captures actor, action, timestamp, reason code, and correlation IDs.
5. **Complete traceability** (§14) — all 20 canonical IDs mapped with primary tests; no orphan DFRs.
6. **Mobile baseline** (§11) — concrete viewport and interaction constraints make the NFR testable.
7. **Clean DFR decomposition** (§4) — 17 DFRs map cleanly to 20 canonical IDs with consistent granularity.

---

## 6. Prioritized Action Plan

| Priority | ID | Action | Effort |
|---|---|---|---|
| P1 | GAP-05-01 | Define explicit quorum ownership boundary with SRS-04; add cross-reference | 0.75h |
| P1 | GAP-05-02 | Define request/response schemas for `resolve_approvers`, `perform_task_action`, `batch_task_action` | 1.5h |
| P1 | GAP-05-03 | Promote 4 planned edge-case tests to §13 acceptance table | 0.5h |
| P1 | GAP-05-04 | Define escalation target resolution contract (source, max depth, guards) | 0.75h |
| P1 | GAP-05-05 | Define `record_field_ref` resolution rules (supported types, null handling, multi-value) | 0.75h |
| P2 | GAP-05-06 | State delegation chain depth policy | 0.25h |
| P2 | GAP-05-07 | Add task state transition matrix | 0.5h |
| P2 | GAP-05-08 | Define `request_changes` lifecycle (resubmission, reviewer assignment) | 0.5h |
| P2 | GAP-05-09 | Expand mobile baseline (tablet, landscape, browser versions) | 0.25h |
| P2 | GAP-05-10 | Clarify anti-self default behavior (remove vs block) | 0.25h |
| P2 | GAP-05-11 | Define relationship with Odoo `mail.followers` system | 0.25h |
| P2 | EC-M1–M10 | Add 10 missing edge cases to register with linked test IDs | 1.0h |

**Total estimated effort:** ~7.25 hours

---

## 7. Verdict

**SRS-05 v1.1-draft is structurally sound with complete canonical coverage.**

Development can begin on approver resolution logic (named user, group, hierarchy), anti-self/SoD policy engine, task creation, and basic task action processing. However, **escalation implementation is blocked** until GAP-05-04 (escalation target resolution) is resolved, **quorum implementation risks duplication** with SRS-04 until GAP-05-01 (ownership boundary) is clarified, and **API integration work requires** GAP-05-02 (API schemas) to avoid rework.

**Recommended path to sign-off:**
1. Resolve the 5 Important items (GAP-05-01 through GAP-05-05).
2. Add the 10 missing edge cases (EC-M1 through EC-M10) to the register.
3. Address the 6 Minor items — particularly GAP-05-07 (state transition matrix) and GAP-05-08 (`request_changes` lifecycle), which are development-blocking despite minor severity classification.
4. Coordinate with SRS-04 on quorum ownership boundary.
5. Add cross-references to SRS-07 (access grants) and SRS-08 (notification delivery).
6. Rerun traceability and test completeness check.
7. Proceed to sign-off.
