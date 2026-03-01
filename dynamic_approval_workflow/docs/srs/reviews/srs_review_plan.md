# SRS Review Plan — Dynamic Approval Workflow Module

**Version:** `v1.0`  
**Date:** `2026-03-01`  
**Project:** Dynamic Approval Workflow Module for Odoo 19  
**Applicable Standard:** ISO/IEC/IEEE 29148:2018 (supersedes IEEE 830-1998)  
**Scope:** Full portfolio review of `SRS-00` through `SRS-10` + parent SRS v1.3

---

## Table of Contents

1. [Purpose and Objectives](#1-purpose-and-objectives)
2. [Review Scope and Document Inventory](#2-review-scope-and-document-inventory)
3. [Review Methodology and Best Practices](#3-review-methodology-and-best-practices)
4. [Quality Criteria — IEEE 29148 Requirement Attributes](#4-quality-criteria--ieee-29148-requirement-attributes)
5. [Review Checklist Per SRS Document](#5-review-checklist-per-srs-document)
6. [Cross-SRS Portfolio Review Checklist](#6-cross-srs-portfolio-review-checklist)
7. [Current Review Status Dashboard](#7-current-review-status-dashboard)
8. [Gap Consolidation and Open Issues](#8-gap-consolidation-and-open-issues)
9. [Review Execution Schedule](#9-review-execution-schedule)
10. [Roles and Responsibilities (RACI)](#10-roles-and-responsibilities-raci)
11. [Entry and Exit Criteria](#11-entry-and-exit-criteria)
12. [Risk Assessment](#12-risk-assessment)
13. [Lessons Learned from Prior Review Iterations](#13-lessons-learned-from-prior-review-iterations)
14. [Requirements Smell Detection Guide](#14-requirements-smell-detection-guide)
15. [Sign-Off Template](#15-sign-off-template)

---

## 1. Purpose and Objectives

### 1.1 Purpose
This document defines the systematic plan for reviewing all SRS documents in the Dynamic Approval Workflow portfolio. It ensures every requirement is validated against industry best practices (ISO/IEC/IEEE 29148:2018) before baseline lock and implementation begins.

### 1.2 Objectives
1. Verify **completeness** — every FR/NFR from parent SRS v1.3 is elaborated in exactly one child SRS.
2. Verify **consistency** — no contradictions between child SRS documents or with the parent.
3. Verify **quality** — each requirement meets the 8 quality attributes defined in §4.
4. Verify **traceability** — every canonical ID has a test case; every DFR maps to a canonical ID.
5. Verify **implementability** — requirements are concrete enough for developers to implement without guessing.
6. Identify and close **open issues** — promote planned-only tests, resolve deferred parameters.
7. Establish **baseline readiness** — produce a signed-off portfolio ready for Phase 1 development.

---

## 2. Review Scope and Document Inventory

### 2.1 Parent Documents

| Document | File | Purpose |
|---|---|---|
| Original Concept SRS | `workflow_srs.md` | Initial brainstorm and concept-level SRS |
| Canonical SRS v1.3 | `dynamic_approval_workflow_srs_v1.3.md` | Source of truth for all FR/NFR IDs |
| Flywheel Kit v1.0 | `dynamic_approval_workflow_flywheel_kit_v1.0.md` | Operating system for continuous improvement |

### 2.2 Governance

| Doc ID | File | Domain |
|---|---|---|
| `SRS-00` | `srs_00_master_traceability.md` | Governance, traceability, requirement ID policy |

### 2.3 Child SRS Documents (SRS-01 through SRS-10)

| Doc ID | File | Domain | FR Scope | Primary Owner |
|---|---|---|---|---|
| `SRS-01` | `srs_01_workflow_definition_versioning.md` | Definition & versioning | `FR-001..006`, `FR-066`, `FR-075`, `FR-086..089`, `NFR-008` | BA |
| `SRS-02` | `srs_02_binding_enforcement_callback.md` | Binding, enforcement, callback | `FR-007..012`, `FR-071..072`, `FR-081`, `FR-090..095`, `NFR-011`, `NFR-017` | Tech Lead |
| `SRS-03` | `srs_03_bpmn_modeling_validation_viewer.md` | BPMN modeler/viewer | `FR-013..020`, `NFR-009` | Tech Lead |
| `SRS-04` | `srs_04_runtime_orchestration_conditions.md` | Runtime orchestration | `FR-021..028`, `FR-073`, `FR-082`, `NFR-002`, `NFR-004` | Tech Lead |
| `SRS-05` | `srs_05_approver_resolution_human_tasks.md` | Approvers & human tasks | `FR-029..042`, `FR-047..050`, `FR-074`, `NFR-014` | BA |
| `SRS-06` | `srs_06_signature_evidence_policy.md` | Signature & evidence | `FR-043..046`, `FR-084..085`, `FR-096`, `NFR-006` | Compliance Lead |
| `SRS-07` | `srs_07_access_security_governance.md` | Access, security, governance | `FR-051..055`, `FR-061..065`, `FR-079`, `NFR-007`, `NFR-010`, `NFR-012` | Security Lead |
| `SRS-08` | `srs_08_notifications_webhooks_external_contracts.md` | Notifications & integration | `FR-056..060`, `FR-083`, `NFR-005` | Integration Lead |
| `SRS-09` | `srs_09_operations_monitoring_retention_reliability.md` | Ops, monitoring, retention | `FR-067..070`, `FR-076..078`, `NFR-001`, `NFR-003`, `NFR-013` | Ops Lead |
| `SRS-10` | `srs_10_data_model_api_test_traceability.md` | Data model, API, test traceability | Contract sections, `NFR-016` | Tech Lead |

### 2.4 Existing Review Artifacts

| Artifact | File | Status |
|---|---|---|
| Review SRS-01 | `review_srs_01.md` | Complete |
| Review SRS-02 | `review_srs_02.md` | Complete |
| Review SRS-03 | `review_srs_03.md` | Complete |
| Review SRS-04 | `review_srs_04.md` | Complete |
| Review SRS-05 | `review_srs_05.md` | Complete |
| Review SRS-06 | `review_srs_06.md` | Complete |
| Review SRS-07 | `review_srs_07.md` | Complete |
| Review SRS-08 | `review_srs_08.md` | Complete |
| Review SRS-09 | `review_srs_09.md` | Complete |
| Review SRS-10 | `review_srs_10.md` | Complete |
| Portfolio Connection Review | `review_full_srs_connection.md` | Complete |
| Agent Review Memory | `agent_srs_review_memory.md` | 7 iterations captured |

### 2.5 Canonical ID Counts
- Functional Requirements: **95 IDs** (`FR-001..FR-096`, with `FR-080` reserved)
- Non-Functional Requirements: **17 IDs** (`NFR-001..NFR-017`)
- Target traceability: **100%** coverage across child SRS and tests

---

## 3. Review Methodology and Best Practices

### 3.1 Review Types (per ISO/IEC/IEEE 29148:2018)

| Review Type | Purpose | When | Participants |
|---|---|---|---|
| **Individual Review** | Each reviewer reads document independently, logs defects | Before group review | All reviewers |
| **Peer/Group Review** | Discuss findings, resolve conflicts, agree on severity | After individual review | BA, Tech Lead, QA, Domain Owner |
| **Cross-Document Review** | Verify consistency, traceability, and contract alignment across all SRS files | After all individual reviews | Tech Lead, BA, QA Lead |
| **Baseline Audit** | Final verification that all gaps are closed, sign-offs collected | Before baseline freeze | All stakeholders |

### 3.2 Review Process Flow

```
  ┌─────────────────────┐
  │ 1. PREPARATION      │  Reviewer reads SRS + parent ref + traceability matrix
  ├─────────────────────┤
  │ 2. INDIVIDUAL CHECK │  Apply §4 quality criteria + §5 checklist per document
  ├─────────────────────┤
  │ 3. DEFECT LOGGING   │  Record gaps in structured format (ID, severity, location)
  ├─────────────────────┤
  │ 4. GROUP REVIEW     │  Walk through defects, classify, agree on actions
  ├─────────────────────┤
  │ 5. REWORK           │  Author updates SRS to address defects
  ├─────────────────────┤
  │ 6. VERIFICATION     │  Reviewer verifies fixes, closes defects
  ├─────────────────────┤
  │ 7. CROSS-SRS CHECK  │  Apply §6 portfolio checklist
  ├─────────────────────┤
  │ 8. BASELINE SIGN-OFF│  Apply §11 exit criteria → §15 sign-off
  └─────────────────────┘
```

### 3.3 Best Practices (Consolidated from IEEE 29148, SWEBOK, BABOK)

1. **Separate "what" from "how"** — requirements describe behavior, not implementation.
2. **One requirement per statement** — avoid compound requirements with "and/or".
3. **Use "shall" for mandatory** — distinguish from "should" (desired) and "may" (optional).
4. **Quantify NFRs** — every performance/reliability requirement needs a measurable threshold.
5. **Test every requirement** — if it can't be tested, it's not a requirement.
6. **Version requirements** — track changes with IDs that never get reused.
7. **Bidirectional traceability** — requirement ↔ test ↔ design artifact.
8. **Avoid requirements smells** — see §14 for detection patterns.
9. **Validate against stakeholders** — requirements must reflect real user needs.
10. **Review iteratively** — don't try to perfect everything in one pass.

---

## 4. Quality Criteria — IEEE 29148 Requirement Attributes

Each individual requirement SHALL be evaluated against these 8 attributes:

| # | Attribute | Definition | Review Question |
|---|---|---|---|
| 1 | **Necessary** | The requirement is essential; removing it would create a deficiency | "Would the system be deficient without this?" |
| 2 | **Appropriate** | The requirement is at the right level of detail for the document scope | "Is this SRS-level, or implementation/design detail?" |
| 3 | **Unambiguous** | The requirement has exactly one interpretation | "Can two developers read this differently?" |
| 4 | **Complete** | The requirement is fully stated with all conditions, constraints, and acceptance criteria | "Are all edge cases, error conditions, and boundaries specified?" |
| 5 | **Singular** | The requirement states a single capability (no compound AND/OR) | "Does this mix multiple requirements?" |
| 6 | **Feasible** | The requirement can be implemented within known constraints | "Can this be built with Odoo 19 + Python + JS within budget?" |
| 7 | **Verifiable** | The requirement can be proven through testing, inspection, or analysis | "Can I write a pass/fail test for this?" |
| 8 | **Traceable** | The requirement has a unique ID and can be linked to source, design, and test | "Does this have a canonical FR/NFR ID with test mapping?" |

### Set-Level Quality Attributes

The requirement SET across each SRS SHALL also satisfy:

| # | Set Attribute | Definition | Review Question |
|---|---|---|---|
| A | **Complete Set** | No missing requirements for the declared scope | "Are there undocumented behaviors the system must support?" |
| B | **Consistent Set** | No contradictions between requirements | "Do any two requirements conflict?" |
| C | **Feasible Set** | The combined requirements can be implemented together | "Do resource/technology constraints make the whole set infeasible?" |
| D | **Comprehensible** | The set is organized and readable by all stakeholders | "Can a new team member understand the SRS within reasonable time?" |

---

## 5. Review Checklist Per SRS Document

Apply this checklist to **each** child SRS (`SRS-01` through `SRS-10`):

### 5.1 Structure and Completeness

- [ ] **SC-01** Document header contains: SRS ID, version, date, status, author, and parent reference.
- [ ] **SC-02** Purpose section clearly defines the domain scope of this child SRS.
- [ ] **SC-03** All canonical FR/NFR IDs assigned to this SRS (per `SRS-00` §7) are present.
- [ ] **SC-04** No extra canonical IDs appear that belong to another SRS.
- [ ] **SC-05** Each canon FR/NFR has at least one derived DFR with format `DFR-<SRS>-<NNN>`.
- [ ] **SC-06** DFR naming is sequential and non-duplicated within the document.
- [ ] **SC-07** Acceptance criteria / test cases exist for every DFR.
- [ ] **SC-08** Edge case register is present and classified by risk impact.
- [ ] **SC-09** Critical/important edge cases are promoted to acceptance tests (not "planned-only").
- [ ] **SC-10** Open issues section exists; each issue has owner, closure artifact, and deadline.

### 5.2 Requirement Quality (per §4 attributes)

- [ ] **RQ-01** Each requirement uses "shall" for mandatory behavior.
- [ ] **RQ-02** No compound requirements (one capability per statement).
- [ ] **RQ-03** No ambiguous adjectives/adverbs (e.g., "fast", "user-friendly", "reasonable").
- [ ] **RQ-04** No subjective language or vague references (e.g., "etc.", "and so on", "appropriate").
- [ ] **RQ-05** All numeric thresholds are explicit (latency, timeouts, limits, retention).
- [ ] **RQ-06** Each requirement is verifiable — a test can be written for it.
- [ ] **RQ-07** No negative requirements without corresponding positive statement.
- [ ] **RQ-08** No implementation-specific language (SQL, class names, method signatures) in requirement statements.
- [ ] **RQ-09** Error/exception behavior is specified for each functional requirement.
- [ ] **RQ-10** Boundary conditions are documented (min, max, empty, null, overflow).

### 5.3 Traceability and Cross-References

- [ ] **TR-01** Traceability matrix section maps every DFR → canonical FR/NFR → test case.
- [ ] **TR-02** No orphaned DFRs (every DFR links to at least one canonical ID).
- [ ] **TR-03** No orphaned test cases (every test maps to a DFR).
- [ ] **TR-04** Cross-SRS dependencies are explicitly stated with target SRS ID and contract name.
- [ ] **TR-05** Shared terms match the portfolio glossary (see §6 checklist).

### 5.4 State Models and Lifecycle

- [ ] **SM-01** State/lifecycle diagrams are present where applicable.
- [ ] **SM-02** All transitions have defined trigger, guard condition, and post-condition.
- [ ] **SM-03** Terminal / error / recovery states are defined.
- [ ] **SM-04** Concurrent state entry has deterministic merge semantics.

### 5.5 NFR Specificity

- [ ] **NF-01** Performance NFRs have measurable thresholds with test profile conditions.
- [ ] **NF-02** Reliability NFRs define target SLO with measurement window.
- [ ] **NF-03** Security NFRs reference specific control mechanisms.
- [ ] **NF-04** Scalability NFRs define load profile and growth assumptions.
- [ ] **NF-05** Compatibility NFRs specify supported platforms/browsers/devices.

---

## 6. Cross-SRS Portfolio Review Checklist

Apply after all individual SRS reviews are complete:

### 6.1 Canonical ID Coverage

- [ ] **PC-01** 100% of `FR-001..FR-096` (excluding reserved `FR-080`) appear in exactly one child SRS.
- [ ] **PC-02** 100% of `NFR-001..NFR-017` appear in at least one child SRS (shared NFRs documented in both).
- [ ] **PC-03** No duplicate canonical ID ownership across SRS files (check `SRS-00` §7 matrix).
- [ ] **PC-04** Deprecated requirements are marked with reason and date, not deleted.

### 6.2 Contract Consistency

- [ ] **CC-01** API/event contracts referenced across multiple SRS files use identical field names and types.
- [ ] **CC-02** State names and transitions are consistent (e.g., `draft`/`published`/`archived` means the same thing everywhere).
- [ ] **CC-03** Idempotency semantics are consistently defined across SRS-01/02/08/10.
- [ ] **CC-04** Incident and recovery patterns align between SRS-02/08/09/10.
- [ ] **CC-05** Retry classification ownership is clear (not split ambiguously between SRS-08 and SRS-09).

### 6.3 Term Normalization

- [ ] **TN-01** A glossary of shared terms exists or is derivable from the documents.
- [ ] **TN-02** Key terms are used consistently: `scope`, `activation`, `incident`, `idempotency_key`, `principal`, `system_attestation`.
- [ ] **TN-03** "Effective-once" vs "exactly-once" wording is normalized with a single reference definition.

### 6.4 Planned-Only Test Promotion

- [ ] **TP-01** No critical-risk edge case remains as "planned-only" test.
- [ ] **TP-02** All high-risk planned tests are either promoted to acceptance criteria or explicitly deferred with risk acceptance.
- [ ] **TP-03** Test promotion status tracked per SRS in the dashboard (§7).

### 6.5 Open Issue Closure

- [ ] **OI-01** Every open issue across all SRS files has an assigned owner.
- [ ] **OI-02** Every open issue has a linked closure artifact (decision record, appendix, or design doc).
- [ ] **OI-03** No blocking open issue remains before baseline freeze.

---

## 7. Current Review Status Dashboard

### 7.1 Individual SRS Review Status

| SRS | Document | Review File | Overall Verdict | Gaps (C/I/M) | Status |
|---|---|---|---|---|---|
| `SRS-00` | Master Traceability | — | Not yet formally reviewed | — | **Pending** |
| `SRS-01` | Definition & Versioning | `review_srs_01.md` | Conditionally Ready | 1 / 5 / 4 | **Needs rework** |
| `SRS-02` | Binding & Enforcement | `review_srs_02.md` | Ready for Development | 0 / 0 / 0 | **Signed off** |
| `SRS-03` | BPMN Modeling | `review_srs_03.md` | Conditionally Ready | 0 / 5 / 6 | **Needs rework** |
| `SRS-04` | Runtime Orchestration | `review_srs_04.md` | Ready for Development | 0 / 0 / 3 | **Signed off** |
| `SRS-05` | Approver & Human Tasks | `review_srs_05.md` | Conditionally Ready | 0 / 5 / 6 | **Needs rework** |
| `SRS-06` | Signature & Evidence | `review_srs_06.md` | Ready for Development | 0 / 1 / 2 | **Minor rework** |
| `SRS-07` | Access & Security | `review_srs_07.md` | Ready for Development | 0 / 1 / 2 | **Minor rework** |
| `SRS-08` | Notifications & Webhooks | `review_srs_08.md` | Ready for Development | 0 / 1 / 2 | **Minor rework** |
| `SRS-09` | Ops & Monitoring | `review_srs_09.md` | Ready for Development | 0 / 1 / 2 | **Minor rework** |
| `SRS-10` | Data Model & API | `review_srs_10.md` | Ready for Development | 0 / 1 / 2 | **Minor rework** |

### 7.2 Portfolio-Level Review

| Review | File | Verdict | Key Finding |
|---|---|---|---|
| Full Connection Review | `review_full_srs_connection.md` | Conditionally Ready | No critical contradictions; planned tests + open issues need closure |

### 7.3 Gap Summary Totals

| Severity | Count | Action Required |
|---|---|---|
| **Critical** | 1 (`SRS-01`: key structure) | Must resolve before any development |
| **Important** | 20 (across SRS-01/03/05/06/07/08/09/10) | Must resolve before baseline freeze |
| **Minor** | 27 (across all) | Should resolve; non-blocking for development start |
| **Total** | 48 | |

---

## 8. Gap Consolidation and Open Issues

### 8.1 Critical Gaps (Must Fix — Blocks Development)

| ID | SRS | Gap | Required Action | Owner | Deadline |
|---|---|---|---|---|---|
| GAP-01-01 | SRS-01 | Definition key structure and ownership model undefined | Add §5.1 with key format, uniqueness scope, ownership fields, cardinality | BA | Before Phase 1 |

### 8.2 Cross-SRS Open Issues (Must Close Before Baseline)

| ID | Source SRS | Issue | Resolution Required | Owner | Target |
|---|---|---|---|---|---|
| OI-01 | SRS-08 / SRS-09 | Retry classification split across two docs | Publish unified retry matrix appendix | Integration Lead + Ops Lead | Week 2 |
| OI-02 | SRS-10 / SRS-09 | Idempotency retention duration unresolved | Finalize with ops/legal alignment and update both docs | Tech Lead + Ops Lead | Week 2 |
| OI-03 | Portfolio | "Effective-once" vs "exactly-once" wording inconsistency | Add glossary entry, normalize across SRS-02/08/10 | Tech Lead | Week 1 |
| OI-04 | SRS-03/05/06/07/08/09/10 | Planned-only edge tests for high-risk scenarios | Promote to acceptance criteria or document risk acceptance | QA Lead per domain | Week 3 |

### 8.3 Conditional SRS Rework Queue

| Priority | SRS | Key Issues | Estimated Effort |
|---|---|---|---|
| 1 | SRS-01 | Critical key structure gap + 5 important gaps | 1-2 days |
| 2 | SRS-05 | Quorum overlap with SRS-04, API contracts, escalation edge tests | 1-2 days |
| 3 | SRS-03 | OWL integration spec, compile handoff, validation schema | 1-2 days |
| 4 | SRS-06..10 | Minor: promote planned tests, clarify operational parameters | 0.5-1 day each |

---

## 9. Review Execution Schedule

### 9.1 Phase 1: Rework and Individual Re-Review (Week 1-2)

| Day | Activity | Participants | Deliverable |
|---|---|---|---|
| D1-D2 | Rework SRS-01 (critical gap + important gaps) | BA, Tech Lead | Updated `srs_01` v1.2 |
| D2-D3 | Re-review SRS-01 against §5 checklist | QA Lead, Tech Lead | Updated `review_srs_01` |
| D3-D4 | Rework SRS-05 (quorum, API, escalation) | BA, Tech Lead | Updated `srs_05` |
| D4-D5 | Rework SRS-03 (OWL, compile, validation) | Tech Lead, UX | Updated `srs_03` |
| D5+ | Minor rework on SRS-06..10 (parallel) | Domain owners | Updated docs |

### 9.2 Phase 2: Cross-SRS Alignment (Week 2-3)

| Day | Activity | Participants | Deliverable |
|---|---|---|---|
| D6 | Resolve OI-01: Unified retry matrix appendix | Integration + Ops Lead | Retry appendix doc |
| D7 | Resolve OI-02: Idempotency retention finalization | Tech + Ops Lead | Updated SRS-09/10 |
| D7 | Resolve OI-03: Glossary normalization | Tech Lead | Glossary appendix |
| D8-D9 | Promote planned-only tests (OI-04) per SRS | QA Lead + domain owners | Updated acceptance sections |
| D10 | Execute §6 portfolio checklist | Tech Lead, BA, QA Lead | Portfolio review update |

### 9.3 Phase 3: Baseline Audit and Sign-Off (Week 3)

| Day | Activity | Participants | Deliverable |
|---|---|---|---|
| D11 | Final §11 exit criteria verification | BA, Tech Lead, QA Lead | Exit criteria checklist |
| D12 | Stakeholder walkthrough and sign-off collection | All stakeholders | Signed §15 forms |
| D13 | Baseline freeze announcement | Product Owner | Baseline notification |

---

## 10. Roles and Responsibilities (RACI)

| Activity | Product Owner | BA | Tech Lead | QA Lead | Security Lead | Compliance Lead | Ops Lead |
|---|---|---|---|---|---|---|---|
| Parent SRS maintenance | **A** | **R** | C | C | C | C | C |
| SRS-00 governance | **A** | R | C | C | I | I | I |
| Child SRS authoring | I | **R** (01,05) | **R** (02,03,04,10) | C | **R** (07) | **R** (06) | **R** (08,09) |
| Individual SRS review | I | **R** | **R** | **R** | R (07) | R (06) | R (08,09) |
| Cross-SRS review | I | C | **R** | **R** | C | C | C |
| Gap rework | I | **R** | **R** | C | R | R | R |
| Test promotion | I | C | C | **R** | C | C | C |
| Baseline sign-off | **A** | **R** | **R** | **R** | **R** | **R** | **R** |

Legend: **R** = Responsible, **A** = Accountable, **C** = Consulted, **I** = Informed

---

## 11. Entry and Exit Criteria

### 11.1 Entry Criteria (To Start Review)

- [x] Parent SRS v1.3 is published and stable.
- [x] SRS-00 master traceability is complete.
- [x] All child SRS documents (SRS-01..SRS-10) exist in at least draft-complete state.
- [x] Reviewers have access to all documents and understand the review checklist.
- [x] Agent review memory from prior iterations is available.

### 11.2 Exit Criteria (To Freeze Baseline)

- [ ] **EX-01** All critical gaps (severity = Critical) are resolved and verified.
- [ ] **EX-02** All important gaps are resolved OR have documented risk acceptance with owner sign-off.
- [ ] **EX-03** 100% canonical FR/NFR IDs have at least one acceptance test.
- [ ] **EX-04** No planned-only tests remain for critical/high-risk edge cases.
- [ ] **EX-05** All cross-SRS open issues (§8.2) are closed with artifacts.
- [ ] **EX-06** Portfolio checklist (§6) passes with no blocking findings.
- [ ] **EX-07** Review reports updated for all reworked SRS documents.
- [ ] **EX-08** Agent review memory updated with final iteration.
- [ ] **EX-09** All stakeholder sign-offs collected (§15 template).
- [ ] **EX-10** Baseline version numbers assigned to all SRS documents.

---

## 12. Risk Assessment

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| SRS-01 critical gap blocks Phase 1 start | High | High | Prioritize SRS-01 rework on Day 1-2 |
| Stakeholder unavailable for sign-off | Medium | Medium | Async review with 48h response SLA |
| Planned test promotion reveals new gaps | Medium | Low | Time-boxed; defer non-critical to post-baseline |
| Cross-SRS contradiction found during portfolio review | Low | High | Already mitigated by `review_full_srs_connection.md`; re-verify after rework |
| Requirements scope creep during rework | Medium | Medium | Rework only addresses documented gaps; new requirements go through change control |
| Agent review memory not consulted | Low | Medium | This plan embeds all learned rules from 7 iterations |

---

## 13. Lessons Learned from Prior Review Iterations

Consolidated from `agent_srs_review_memory.md` (7 iterations):

### 13.1 Recurring Patterns to Watch

| Pattern | Frequency | Rule |
|---|---|---|
| Edge cases left as "planned-only" instead of acceptance tests | 7/7 iterations | Critical/important edge paths must be acceptance tests |
| NFR without concrete measurement threshold | 3/7 | Every NFR needs measurable dataset/conditions |
| Cross-SRS dependencies not explicitly referenced | 4/7 | State destination SRS, contract name, and closure condition |
| Race condition ordering undocumented | 2/7 | Deterministic ordering for concurrent flows must be in main body |
| Open issues without owner or closure artifact | 5/7 | Every open issue needs owner + closure artifact + deadline |
| Governance responsibilities implicit | 2/7 | Include RACI for governance controls |
| Numeric thresholds missing for ops/reliability | 2/7 | Pin exact values, not just "should be fast" |

### 13.2 Reviews That Improved Most

| SRS | Pre-review Gaps | Post-rework Gaps | Improvement |
|---|---|---|---|
| SRS-04 | 14 gaps (initial) | 3 minor | Best in class — full gap closure |
| SRS-02 | Multiple (initial) | 0 | Clean sign-off achieved |

### 13.3 Reviews Still Needing Most Work

| SRS | Current Gaps | Key Blocker |
|---|---|---|
| SRS-01 | 10 (1C, 5I, 4M) | Critical key structure definition |
| SRS-05 | 11 (5I, 6M) | Quorum/escalation contracts |
| SRS-03 | 11 (5I, 6M) | OWL integration and validation schema |

---

## 14. Requirements Smell Detection Guide

Based on research (Femmer et al., 2017 — "Rapid quality assurance with Requirements Smells") and ISO/IEC/IEEE 29148:

### 14.1 Language Smells (Flag During Review)

| Smell | Examples | Fix |
|---|---|---|
| **Subjective language** | "user-friendly", "easy to use", "intuitive" | Replace with measurable criteria |
| **Ambiguous adverbs/adjectives** | "quickly", "efficiently", "flexibly" | Add numeric threshold or remove |
| **Superlatives** | "best", "fastest", "most secure" | Replace with specific measurable target |
| **Comparative without baseline** | "faster than current", "better performance" | State absolute target and current baseline |
| **Negative statements** | "shall not crash", "must not fail" | Rewrite as positive behavior specification |
| **Loopholes** | "if applicable", "where possible", "as needed" | State exact conditions or remove qualifier |
| **Vague pronouns** | "it", "this", "they" without clear antecedent | Name the specific entity |
| **Unbounded lists** | "etc.", "and so on", "including but not limited to" | Enumerate all items or define explicit scope |
| **Passive voice** | "shall be processed" (by whom?) | "The system shall process..." |
| **Totality terms** | "always", "never", "all", "none" | Verify absolute claim is truly absolute, or add conditions |

### 14.2 Structural Smells

| Smell | Symptom | Fix |
|---|---|---|
| **Compound requirement** | "shall X and Y and Z" | Split into `FR-A`, `FR-B`, `FR-C` |
| **Missing error path** | Only happy path described | Add "If [error], then [behavior]" |
| **Unverifiable requirement** | No test can prove compliance | Add measurable acceptance criterion |
| **Orphaned requirement** | No source (why?) or no test (how to verify?) | Add traceability link |
| **Gold-plated requirement** | Not traceable to any stakeholder need | Challenge necessity; remove or defer |

---

## 15. Sign-Off Template

### Per-Document Sign-Off

```
SRS Document:   [SRS-XX]
Version:        [vX.Y]
Review Date:    [YYYY-MM-DD]
Review Report:  [review_srs_XX.md]

□ All checklist items in §5 verified
□ All critical/important gaps resolved
□ Agent memory updated for this iteration
□ Traceability matrix is complete

Reviewer:       ________________  Date: __________  Signature: __________
Domain Owner:   ________________  Date: __________  Signature: __________
QA Lead:        ________________  Date: __________  Signature: __________
```

### Portfolio Baseline Sign-Off

```
Portfolio:      Dynamic Approval Workflow SRS
Baseline Ver:   [vX.Y]
Sign-Off Date:  [YYYY-MM-DD]

□ All §11.2 exit criteria met
□ All §6 portfolio checks passed
□ No unresolved critical or important gaps
□ Agent review memory finalized

Product Owner:    ________________  Date: __________  Signature: __________
BA Lead:          ________________  Date: __________  Signature: __________
Tech Lead:        ________________  Date: __________  Signature: __________
QA Lead:          ________________  Date: __________  Signature: __________
Security Lead:    ________________  Date: __________  Signature: __________
Compliance Lead:  ________________  Date: __________  Signature: __________
Ops Lead:         ________________  Date: __________  Signature: __________
```

---

## Appendix A: Document References

1. ISO/IEC/IEEE 29148:2018 — Systems and software engineering — Requirements engineering
2. IEEE 830-1998 — Recommended Practice for Software Requirements Specifications (superseded)
3. SWEBOK v3 — Guide to the Software Engineering Body of Knowledge, Chapter 1: Software Requirements
4. BABOK v3 — Business Analysis Body of Knowledge, Chapter 7: Requirements Analysis and Design Definition
5. Femmer et al. (2017) — "Rapid quality assurance with Requirements Smells", JSS 123:190-213
6. `dynamic_approval_workflow_srs_v1.3.md` — Parent canonical SRS
7. `srs_00_master_traceability.md` — Governance and traceability contract
8. `agent_srs_review_memory.md` — Iterative review lessons (7 iterations)
9. `review_full_srs_connection.md` — Cross-SRS portfolio connection review
10. `dynamic_approval_workflow_flywheel_kit_v1.0.md` — Continuous improvement operating system
