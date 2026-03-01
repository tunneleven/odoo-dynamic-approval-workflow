# SRS-04 Review Report: Runtime Orchestration and Conditions

## Review History

| Review | Version | Date | Verdict | Score |
|---|---|---|---|---|
| Initial Review | `v1.0-draft` | 2026-02-27 | NOT READY — 5 Critical, 6 Important, 3 Minor gaps | 6.4/10 |
| **Re-Review** | **`v1.1-draft`** | **2026-02-27** | **READY FOR DEVELOPMENT — 3 Minor residual observations** | **8.7/10** |

**Reviewer:** AI Spec Reviewer  
**Document Under Review:** `srs_04_runtime_orchestration_conditions.md` (`v1.1-draft`)  
**Baseline References:** `dynamic_approval_workflow_srs_v1.3.md`, `srs_00_master_traceability.md`

---

## Executive Summary

**Overall Assessment: READY FOR DEVELOPMENT — Minor Polish Items Only**

The v1.1-draft comprehensively addresses all 14 gaps raised in the initial review. Every P0 critical gap is fully resolved. All P1 important gaps are resolved. All P2 minor gaps are resolved. The document grew from ~280 lines to 491 lines, with substantial new sections for token lifecycle (§5.4), node state machine (§5.3), condition runtime contract (§7.5), quorum outcome resolution (§8.4), rework in parallel context (§10.3), simulation detail (§11.1-§11.6), concurrency controls (§12.4), signal semantics (§6.5), incident resolution (§6.6), and cancellation transitions (§5.2.2).

Test scenarios expanded from 18 to 29, edge cases from 7 to 16, and runtime events from 7 to 12. Two new DFRs were added (`DFR-04-013`, `DFR-04-014`). The previously-blocking Open Issue #1 (quorum snapshot policy) has been resolved in §8.3.

**3 minor residual observations** remain — none are development-blocking.

---

## 1. Gap Resolution Verification

### 1.1 P0 Critical Gaps — ALL RESOLVED

| Gap ID | Original Issue | Resolution Location | Verdict | Notes |
|---|---|---|---|---|
| GAP-01 | Token lifecycle undefined | §5.4 (Token Lifecycle) | ✅ **RESOLVED** | Token data contract (9 fields), 5 transition rules covering sequential/split/all/quorum/any, persistence rule. `any` join cancellation behavior is explicit and includes task/timer side-effects. |
| GAP-02 | Node state machine not formalized | §5.3 (Node State Machine) | ✅ **RESOLVED** | 5-row transition table with triggers, preconditions, and notes. 2 invariants clearly separating terminal states from rework-as-new-record semantics. |
| GAP-03 | `any` join remaining branch handling | §5.4.2 item 5 + §8.1 item 2 | ✅ **RESOLVED** | Remaining tokens → `cancelled` with `branch_superseded`. Node_runtimes → `skipped`. Tasks cancelled with reason. Timers deactivated. Qualifying outcome set configurable (`approve_only`, `reject_only`, `any_outcome`). |
| GAP-04 | Rework + parallel interaction | §10.3 (Rework in Parallel Context) | ✅ **RESOLVED** | 5 rules covering cross-branch rework (cancels siblings), same-branch rework, new node_runtime records, approver re-resolution (cross-ref SRS-05), record snapshot refresh. |
| GAP-05 | Condition expression format missing | §7.5 (Condition Runtime Contract) | ✅ **RESOLVED** | JSON rule tree shape (connector + rules), 12-operator minimum set, null/missing policy, type coercion policy (no implicit coercion), relational traversal depth limit (3 hops), ownership boundary cross-ref to SRS-03/SRS-10. Appropriately keeps full schema ownership out of SRS-04 per counter-argument. |

### 1.2 P1 Important Gaps — ALL RESOLVED

| Gap ID | Original Issue | Resolution Location | Verdict | Notes |
|---|---|---|---|---|
| GAP-06 | Quorum mixed outcomes unclear | §8.4 (Quorum Outcome Resolution) | ✅ **RESOLVED** | Approval quorum + optional rejection quorum. Mixed outcome priority rule. Dynamic impossibility detection. Timeout decisions count toward quorum (configurable). |
| GAP-07 | Rework loop details too thin | §10.1, §10.2, §10.4 | ✅ **RESOLVED** | Design-time target config (§10.1). Default loop cap 5, range 1-99 (§10.2). Mandatory `change_request_notes`, `loop_iteration` counter, audit event fields (§10.4). |
| GAP-08 | Simulation too skeletal | §11.1-§11.6 | ✅ **RESOLVED** | Context inputs (§11.1), execution model with synthetic decision vectors (§11.2), 5 coverage metrics (§11.3), 4 publish blocking rules (§11.4), report schema contract (§11.5), performance constraint (§11.6). |
| GAP-09 | Lock mechanism unspecified | §12.4 (Concurrency Control Requirements) | ✅ **RESOLVED** | 5 behavioral constraints (per-instance serialization, timeout/retry/backoff, incident on failure, lock window boundary, implementation-agnostic). Good approach — keeps tech-neutral per counter-argument while providing testable requirements. |
| GAP-10 | Cancellation semantics missing | §5.2.2, §12.3 item 3 | ✅ **RESOLVED** | Two cancellation transition rows added (waiting_human/waiting_timer → cancelled). Cancel during active tick queued per §12.3.3. `cancel.requested` added to triggers (§6.1). `cancel_instance` added to API (§13.1). |
| GAP-11 | Incident recovery path missing | §6.6, §5.2.2 | ✅ **RESOLVED** | Admin can retry or cancel. Retry resumes from failed context. Repeated failure escalates. Two transition rows added (error_incident → running, error_incident → cancelled). `retry_incident` added to API (§13.1). |

### 1.3 P2 Minor Gaps — ALL RESOLVED

| Gap ID | Original Issue | Resolution Location | Verdict | Notes |
|---|---|---|---|---|
| GAP-12 | Signal semantics undefined | §6.5 (Signal Semantics) | ✅ **RESOLVED** | 3 signal categories, matching keys, consumable node constraint, unknown signal handling with audit warning. |
| GAP-13 | Timeout configuration scope missing | §9.4 (Timeout Configuration Scope) | ✅ **RESOLVED** | Per-step scope. Calendar-time default. Business-hours deferred to Open Issues. SRS-05 cross-ref for reminders/escalation. |
| GAP-14 | Runtime events incomplete | §13.2 | ✅ **RESOLVED** | Expanded from 7 to 12 events. Added: `workflow.instance.cancelled`, `workflow.node.skipped`, `workflow.task.cancelled`, `workflow.node.rework_initiated`, `workflow.signal.received`. |

### 1.4 Cross-Cutting Updates — ALL ADDRESSED

| Update Area | Status | Details |
|---|---|---|
| Acceptance tests (§14) | ✅ **ADDRESSED** | Expanded from 18 to 29 test scenarios. Promoted planned tests now appear in table. |
| Edge cases (§15) | ✅ **ADDRESSED** | Expanded from 7 to 16 cases (EC-04-01 through EC-04-16). All 9 proposed missing cases incorporated. |
| Traceability (§16) | ✅ **ADDRESSED** | Re-mapped with new sections (§5.4, §7.5, §10.3) and new tests. DFR-04-013 and DFR-04-014 canonical IDs covered through parent FR/NFR mappings. |
| Open issues (§18) | ✅ **ADDRESSED** | Original OI #1 (quorum recomputation) resolved in §8.3 with `freeze_at_assignment` default. Remaining 3 issues are genuine deferrals. |
| DFR additions | ✅ **GOOD** | Two new DFRs (DFR-04-013, DFR-04-014) codify token lifecycle and node state machine as explicit derived requirements. |
| Version/date bump | ✅ **GOOD** | Version `v1.0-draft` → `v1.1-draft`, date updated to 2026-02-27. |
| Scope statement (§2) | ✅ **GOOD** | Updated to include cancellation, incident recovery, and rework-in-parallel. |

---

## 2. Residual Observations (Non-Blocking)

### OBS-01 — 3 Planned Tests Still Not in §14 (MINOR)

**Location:** §15 edge cases EC-04-10, EC-04-11, EC-04-13  
**Issue:** Three edge cases reference test IDs marked "(planned)" that are absent from the acceptance criteria table (§14):
- `TC-X-04-003` (EC-04-10 — record deleted during active runtime)
- `TC-FR-023-004` (EC-04-11 — degenerate gateway with single path)
- `TC-X-04-004` (EC-04-13 — empty approver set at activation)

**Impact:** Non-blocking. The edge cases themselves are well-defined. These are legitimate future test slots.

**Recommendation:** Either promote to §14 or add a note that these are deferred to implementation test planning.

---

### OBS-02 — Quorum Early-Close: Remaining Task Cleanup Not Explicit (MINOR)

**Location:** §5.4.2 item 4, §8.4  
**Issue:** §8.4 says "approval quorum can close step early when met." §5.4.2 item 4 says quorum join "consumes qualifying tokens and resolves per quorum policy." However, the spec doesn't explicitly state what happens to **remaining pending tasks from approvers who haven't yet decided** when the quorum closes early.

Unlike the `any` join (§5.4.2 item 5) which has an explicit 5-point cancellation sequence (tokens, node_runtimes, tasks, timers, notifications), the quorum early-close has no equivalent cleanup specification.

The behavior is **inferable** from the `any` join precedent, but the inference gap exists.

**Impact:** Minor ambiguity. A developer would reasonably infer the matching pattern, but an explicit statement removes guesswork.

**Recommendation:** Add one sentence to §8.4: "When quorum closes a step early, remaining pending tasks are cancelled with `reason_code = quorum_reached` and corresponding timers deactivated, following the cancellation semantics defined in §5.4.2 item 5."

---

### OBS-03 — "Decision Vector" Term Undefined in Simulation (MINOR)

**Location:** §11.2 item 2  
**Issue:** "Human task outcomes are represented by synthetic decision vectors" uses the term "decision vector" without definition. The meaning is inferable (a set of predefined outcomes applied to each human task node during simulation), but the term is jargon-like and not defined elsewhere in the SRS set.

**Impact:** Cosmetic clarity issue. Meaning is inferable from context.

**Recommendation:** Replace with: "Human task outcomes are represented by synthetic decision sets: each human task node is simulated with configurable outcome combinations (approve, reject, request_changes) to maximize path coverage."

---

## 3. Updated Requirement Coverage (PASS)

| Canonical ID | DFR IDs | Sections | Test Count | Verdict |
|---|---|---|---|---|
| `FR-021` | `DFR-04-001`, `DFR-04-014` | §4, §5, §6 | 1 | ✅ |
| `FR-022` | `DFR-04-002`, `DFR-04-013` | §4, §5.4, §6.4, §10.3 | 4 | ✅ |
| `FR-023` | `DFR-04-003` | §4, §7 | 3 | ✅ |
| `FR-024` | `DFR-04-004`, `DFR-04-013` | §4, §8 | 6 | ✅ |
| `FR-025` | `DFR-04-005`, `DFR-04-014` | §4, §10 | 3 | ✅ |
| `FR-026` | `DFR-04-006` | §4, §7.5 | 2 | ✅ |
| `FR-027` | `DFR-04-007` | §4, §7 | 1 | ✅ |
| `FR-028` | `DFR-04-008` | §4, §11 | 2 | ✅ |
| `FR-073` | `DFR-04-009` | §4, §9 | 3 | ✅ |
| `FR-082` | `DFR-04-010` | §4, §8 | 5 | ✅ |
| `NFR-002` | `DFR-04-012` | §4, §12 | 1 | ✅ |
| `NFR-004` | `DFR-04-011`, `DFR-04-013`, `DFR-04-014` | §4, §5.3, §5.4, §12 | 2 | ✅ |

**Total: 12/12 canonical IDs covered. 14 DFRs (up from 12). 29 test scenarios (up from 18).**

---

## 4. Structural Quality Assessment (Updated)

### 4.1 Strengths (v1.1)

1. **Token lifecycle (§5.4)** — Complete data contract (9 fields), 5 transition rules with explicit per-join-mode behavior, persistence guarantee. This fixes the single biggest gap from v1.0.
2. **Node state machine (§5.3)** — Now matches the quality standard set by the instance state machine (§5.2). Transition table with preconditions and notes. Invariants are clean.
3. **Condition runtime contract (§7.5)** — JSON rule tree shape, 12-operator set, null/type-coercion policies, and relational traversal limit provide a clear consumption contract without duplicating builder ownership.
4. **Quorum outcome resolution (§8.4)** — Approval + rejection quorum, mixed outcome priority, dynamic impossibility detection, and timeout counting policy. Comprehensive.
5. **Rework in parallel (§10.3)** — Addresses the highest-impact real-world scenario (e.g., Finance approves, Legal requests changes). Cross-branch vs. same-branch rules are clear.
6. **Simulation (§11)** — Now has 6 subsections covering inputs, execution model, metrics, blocking rules, report schema, and performance. Adequate for development.
7. **Cancellation and incident recovery (§5.2.2, §6.6)** — Complete transition coverage with terminal and recovery paths.
8. **Eligible set snapshot policy (§8.3)** — Resolves original Open Issue #1 with `freeze_at_assignment` default and `recompute_on_event` opt-in. Good governance decision.
9. **Event coverage (§13.2)** — 12 events now cover the full lifecycle including cancellation, skip, rework, and signals.

### 4.2 Consistency Check

| Check | v1.0 Status | v1.1 Status |
|---|---|---|
| §5.2.2 transition table completeness | ⚠️ Missing cancelled, rejected, recovery | ✅ All paths covered |
| §5.3 vs §5.2 quality parity | ⚠️ Node states were just a list | ✅ Both have formal transition tables |
| §13.2 event completeness | ⚠️ Missing 5 events | ✅ All lifecycle events present |
| Open Issue #1 impact on §8.3 | ⚠️ Rule referenced but undefined | ✅ Resolved in §8.3 |
| DFR-to-canonical mapping | ✅ Complete | ✅ Complete + 2 new DFRs |
| Cancel request trigger in §6.1 | ⚠️ Missing | ✅ `cancel.requested` added |
| Cancel/retry API operations | ⚠️ Missing | ✅ `cancel_instance`, `retry_incident` added |

**No internal inconsistencies remain.**

---

## 5. Cross-SRS Interface Clarity (Updated)

| Interface | SRS-04 Side | Other SRS | v1.0 Status | v1.1 Status |
|---|---|---|---|---|
| Condition expression format | §7.5 runtime contract | SRS-03/SRS-10 | ❌ Undefined | ✅ Resolved |
| Approver resolution at step activation | Task creation + rework re-resolution | SRS-05 | ⚠️ Ambiguous | ✅ Cross-ref in §10.3 |
| Task lifecycle | References `decision_event` | SRS-05 | ✅ | ✅ |
| Cancellation runtime effects | §5.2.2, §12.3, §13.1 | SRS-02 (`FR-071`) | ❌ Missing | ✅ Resolved |
| Notification dispatch | Events in tick step 7 | SRS-08 | ✅ | ✅ |
| Incident escalation routing | §6.6 + §18 OI #3 | SRS-09 | ⚠️ Unclear | ✅ Cross-ref |

---

## 6. Development Readiness Scorecard

| Criterion | v1.0 Score | v1.1 Score | Delta |
|---|---|---|---|
| Requirement traceability | 9/10 | 10/10 | +1 |
| State machine completeness | 6/10 | 9/10 | +3 |
| Algorithm determinism | 8/10 | 9/10 | +1 |
| Cross-SRS interface contracts | 5/10 | 8/10 | +3 |
| Edge case coverage | 7/10 | 9/10 | +2 |
| Test scenario coverage | 6/10 | 9/10 | +3 |
| Implementability | 5/10 | 8/10 | +3 |
| **Weighted Overall** | **6.4/10** | **8.7/10** | **+2.3** |

---

## 7. Open Issue Commentary (Updated)

| Open Issue (§18) | Assessment |
|---|---|
| #1 — Business-hours timeout mode deferred | **Acceptable.** Calendar-time default specified; business-hours correctly flagged as future. |
| #2 — Performance benchmark profile for NFR-002 | **Non-blocking for development.** Blocking for acceptance testing. Can be finalized during implementation. |
| #3 — Ops escalation routing matrix | **Non-blocking.** Correctly deferred to SRS-09. |

**No open issues are blocking for development.**

---

## 8. Verdict

**SRS-04 v1.1-draft is READY FOR DEVELOPMENT.**

All 14 gaps from the initial review are fully resolved. The document is now comprehensive, internally consistent, and provides deterministic behavioral rules for every runtime scenario. The 3 residual observations (OBS-01 through OBS-03) are minor polish items that can be addressed during implementation without blocking development.

**Quality improvement**: Score rose from **6.4/10 to 8.7/10** (+2.3 points), driven primarily by the formalized token lifecycle, node state machine, condition runtime contract, and expanded simulation/rework/cancellation coverage.

| Metric | v1.0 | v1.1 | Change |
|---|---|---|---|
| Document lines | ~280 | 491 | +75% |
| DFRs | 12 | 14 | +2 |
| Test scenarios | 18 | 29 | +61% |
| Edge cases | 7 | 16 | +129% |
| Runtime events | 7 | 12 | +71% |
| Critical gaps | 5 | 0 | -100% |
| Important gaps | 6 | 0 | -100% |

**Recommended next steps:**
1. Optionally address OBS-01 (promote 3 planned tests, ~15min), OBS-02 (quorum early-close sentence, ~5min), and OBS-03 (clarify "decision vector" term, ~5min).
2. Proceed to development with SRS-04 v1.1 as the specification baseline.
3. Proceed to drafting `SRS-02` (Binding, Enforcement, Callback) as indicated in §19.
