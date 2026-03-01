# Dynamic Approval Workflow — SRS Document Index

Date: `2026-03-01`  
Status: `baseline-ready-pending-2-blocking-issues`

## Directory Structure

```
srs/
├── README.md                          ← This file
├── baseline/                          ← Parent SRS + governance
│   ├── dynamic_approval_workflow_srs_v1.3.md   (canonical parent)
│   ├── dynamic_approval_workflow_srs_v1.1.md   (legacy snapshot)
│   └── srs_00_master_traceability.md           (governance & traceability)
├── detailed/                          ← Child SRS-01..10
│   ├── srs_01_workflow_definition_versioning.md
│   ├── srs_02_binding_enforcement_callback.md
│   ├── srs_03_bpmn_modeling_validation_viewer.md
│   ├── srs_04_runtime_orchestration_conditions.md
│   ├── srs_05_approver_resolution_human_tasks.md
│   ├── srs_06_signature_evidence_policy.md
│   ├── srs_07_access_security_governance.md
│   ├── srs_08_notifications_webhooks_external_contracts.md
│   ├── srs_09_operations_monitoring_retention_reliability.md
│   └── srs_10_data_model_api_test_traceability.md
├── reviews/                           ← Review artifacts
│   ├── review_consolidated_report.md          ← Full portfolio review (2026-03-01)
│   ├── review_full_srs_connection.md          ← Cross-SRS consistency review
│   ├── review_srs_01.md .. review_srs_10.md   ← Per-document reviews
│   └── srs_review_plan.md                     ← Review plan & checklists
└── supplementary/                     ← Supporting artifacts
    ├── agent_srs_review_memory.md             ← Iterative review lessons (8 iterations)
    └── brainstorm_orm_enforcement_without_model_changes.md
```

## Folder Descriptions

### `baseline/`
Parent-level SRS documents and governance controls. The canonical source of all `FR-*` and `NFR-*` requirement IDs.

| File | Purpose |
|---|---|
| `dynamic_approval_workflow_srs_v1.3.md` | Canonical parent SRS — source of truth for 95 FRs + 17 NFRs |
| `dynamic_approval_workflow_srs_v1.1.md` | Legacy snapshot (superseded) |
| `srs_00_master_traceability.md` | Governance, requirement ID policy, traceability matrix, change control |

### `detailed/`
Child SRS documents elaborating each capability domain. Each maps to a subset of canonical IDs from the parent.

| File | Domain | Key FR Scope |
|---|---|---|
| `srs_01_*` | Definition & versioning | FR-001..006, FR-066, FR-075, FR-086..089, NFR-008 |
| `srs_02_*` | Binding, enforcement, callback | FR-007..012, FR-071..072, FR-081, FR-090..095, NFR-011, NFR-017 |
| `srs_03_*` | BPMN modeler & viewer | FR-013..020, NFR-009 |
| `srs_04_*` | Runtime orchestration | FR-021..028, FR-073, FR-082, NFR-002, NFR-004 |
| `srs_05_*` | Approvers & human tasks | FR-029..042, FR-047..050, FR-074, NFR-014 |
| `srs_06_*` | Signature & evidence | FR-043..046, FR-084..085, FR-096, NFR-006 |
| `srs_07_*` | Access, security, governance | FR-051..055, FR-061..065, FR-079, NFR-007, NFR-010, NFR-012 |
| `srs_08_*` | Notifications & webhooks | FR-056..060, FR-083, NFR-005 |
| `srs_09_*` | Ops, monitoring, retention | FR-067..070, FR-076..078, NFR-001, NFR-003, NFR-013, NFR-015 |
| `srs_10_*` | Data model, API, test traceability | Cross-cutting contracts, NFR-016 |

### `reviews/`
All review artifacts including per-document reviews, portfolio-level reviews, and the review plan.

| File | Purpose |
|---|---|
| `review_consolidated_report.md` | **Primary** — Full portfolio review with gap register, action plan, exit criteria |
| `review_full_srs_connection.md` | Cross-SRS consistency and contract alignment check |
| `review_srs_01.md` .. `review_srs_10.md` | Individual document reviews |
| `srs_review_plan.md` | Review methodology, checklists, schedule, RACI, sign-off templates |

### `supplementary/`
Supporting artifacts for iterative improvement and design exploration.

| File | Purpose |
|---|---|
| `portfolio_glossary.md` | **Normative** — Shared term definitions for the SRS portfolio |
| `srs_to_development_bridge_plan.md` | **Normative** — Document pipeline from SRS to AI-driven development (SDS → OMB → ITM) |
| `agent_srs_review_memory.md` | Lessons learned across 9 review iterations |
| `brainstorm_orm_enforcement_without_model_changes.md` | Design exploration for generic server interceptor |

## Traceability Rules
1. Every detailed SRS must map to inherited `FR-*` and `NFR-*` from `baseline/dynamic_approval_workflow_srs_v1.3.md`.
2. No orphan requirement is allowed.
3. Cross-SRS consistency must be validated through `reviews/review_full_srs_connection.md` before baseline lock.
4. Portfolio-level readiness assessed in `reviews/review_consolidated_report.md`.
