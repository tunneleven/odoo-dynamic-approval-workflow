# Requirements-to-Test Matrix (RTM) — Dynamic Approval Workflow

Version: `v1.0`  
Date: `2026-03-01`  
Owner: `QA Lead`  
Status: `baselined`

---

## 1. Purpose

Provide a single traceability matrix linking:

1. Requirement (`FR-*`/`NFR-*`)
2. Design (`SDS`/`OMB`)
3. Implementation (`TASK-*`, source files)
4. Validation (`TC-*`)
5. Evidence (execution logs/reports)

This document is the required proof layer for release readiness.

## 2. Update Rules

1. One row per requirement ID in release scope.
2. A row is `Pass` only when at least one mapped test has passing evidence.
3. `Blocked` rows require linked blocker/defect IDs.
4. Waivers require explicit approval and expiration date in Notes.
5. Update timestamp and owner on every status change.

## 3. Status Legend

| Status | Meaning |
|---|---|
| Not Run | Test mapped but not yet executed |
| Pass | Execution evidence confirms expected behavior |
| Fail | Test executed and requirement not satisfied |
| Blocked | Cannot execute due to dependency or environment issue |
| Waived | Known gap accepted temporarily by authorized owner |

## 4. Matrix Columns

| Column | Description |
|---|---|
| Requirement ID | `FR-*` or `NFR-*` from baseline SRS |
| DFR Reference | Detailed requirement reference from child SRS |
| Design Reference | `SDS`/`OMB` section IDs |
| Implementation Reference | `TASK-*` and source file links |
| Test Case IDs | `TC-*` list |
| Execution Type | Automated or Manual |
| Last Run Evidence | CI run URL, report ID, or artifact link |
| Status | Not Run / Pass / Fail / Blocked / Waived |
| Owner | Role accountable for row state |
| Updated At | `YYYY-MM-DD` |
| Notes | Defect ID, waiver, or context |

---

## 5. Traceability Matrix

### 5.1 SRS-01 — Definition and Versioning

| Req ID | DFR Ref | Design Ref | Impl Ref | TC IDs | Exec | Evidence | Status | Owner | Updated | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| FR-001 | DFR-01-001 | SDS §4, OMB-01 §1 | TASK-P1-002, `models/workflow_definition.py` | TC-FR-001-001, TC-FR-001-002 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-002 | DFR-01-002 | SDS §4, OMB-01 §3 | TASK-P1-003, `models/workflow_definition_version.py` | TC-FR-002-001, TC-FR-002-002 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-003 | DFR-01-003 | SDS §4, OMB-01 §3 | TASK-P1-003, `models/workflow_definition_version.py` | TC-FR-003-001, TC-FR-003-002 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-004 | DFR-01-004 | SDS §4, OMB-01 §3 | TASK-P1-003, `models/workflow_definition_version.py` | TC-FR-004-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-005 | DFR-01-005 | SDS §4, OMB-01 §1 | TASK-P1-002, `models/workflow_definition.py` | TC-FR-005-001, TC-FR-005-002 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-006 | DFR-01-006 | SDS §4, OMB-01 §2 | TASK-P1-002, `models/workflow_definition.py` | TC-FR-006-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-066 | DFR-01-007 | SDS §16, OMB-02 §1 | TASK-P1-009, `views/workflow_definition_views.xml` | TC-FR-066-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-075 | DFR-01-008 | SDS §15, OMB-03 §1 | TASK-P1-008, `security/ir.model.access.csv` | TC-FR-075-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-086 | DFR-01-009 | SDS §4, OMB-01 §3 | TASK-P1-003, `models/workflow_definition_version.py` | TC-FR-086-001 | Auto | — | Not Run | QA | 2026-03-01 | |

### 5.2 SRS-02 — Binding, Enforcement, Callback

| Req ID | DFR Ref | Design Ref | Impl Ref | TC IDs | Exec | Evidence | Status | Owner | Updated | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| FR-007 | DFR-02-001 | SDS §7, OMB-01 §5 | TASK-P2-001, `models/workflow_binding.py` | TC-FR-007-001, TC-FR-007-002 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-008 | DFR-02-002 | SDS §7, OMB-01 §7 | TASK-P2-002, `models/workflow_enforcement_interceptor.py` | TC-FR-008-001, TC-FR-008-002 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-009 | DFR-02-003 | SDS §7, OMB-01 §7 | TASK-P2-002, `models/workflow_enforcement_interceptor.py` | TC-FR-009-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-010 | DFR-02-004 | SDS §7, OMB-01 §7 | TASK-P2-002, `models/workflow_enforcement_interceptor.py` | TC-FR-010-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-011 | DFR-02-005 | SDS §7, OMB-01 §5 | TASK-P2-001, `models/workflow_binding.py` | TC-FR-011-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-012 | DFR-02-006 | SDS §7, OMB-01 §5 | TASK-P2-001, `models/workflow_binding.py` | TC-FR-012-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-071 | DFR-02-007 | SDS §7, OMB-01 §29 | TASK-P2-004, `models/workflow_approval_mixin.py` | TC-FR-071-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-072 | DFR-02-008 | SDS §7, OMB-01 §5 | TASK-P2-001, `models/workflow_binding.py` | TC-FR-072-001 | Auto | — | Not Run | QA | 2026-03-01 | Callback configuration |
| FR-081 | DFR-02-009 | SDS §7, OMB-01 §7 | TASK-P2-002, `models/workflow_enforcement_interceptor.py` | TC-FR-081-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-090 | DFR-02-010 | SDS §7, OMB-01 §5 | TASK-P2-001, `models/workflow_binding.py` | TC-FR-090-001 | Auto | — | Not Run | QA | 2026-03-01 | |

### 5.3 SRS-03 — BPMN Modeling and Validation

| Req ID | DFR Ref | Design Ref | Impl Ref | TC IDs | Exec | Evidence | Status | Owner | Updated | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| FR-013 | DFR-03-001 | SDS §5, OMB-05 §3 | TASK-P3-008, `static/src/components/bpmn_modeler/` | TC-FR-013-001, TC-FR-013-002 | Manual+Auto | — | Not Run | QA | 2026-03-01 | |
| FR-014 | DFR-03-002 | SDS §5, OMB-05 §1 | TASK-P3-007, `models/workflow_diagram_asset.py` | TC-FR-014-001, TC-FR-014-002 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-015 | DFR-03-003 | SDS §5, OMB-05 §1 | TASK-P3-007, `models/workflow_diagram_asset.py` | TC-FR-015-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-016 | DFR-03-004 | SDS §5.4, OMB-05 §4 | TASK-P3-009, `static/src/components/bpmn_viewer/` | TC-FR-016-001, TC-FR-016-002 | Manual | — | Not Run | QA | 2026-03-01 | |
| FR-017 | DFR-03-005 | SDS §5, OMB-05 §1 | TASK-P3-007, `models/workflow_diagram_asset.py` | TC-FR-017-001 | Auto | — | Not Run | QA | 2026-03-01 | |

### 5.4 SRS-04 — Runtime Orchestration

| Req ID | DFR Ref | Design Ref | Impl Ref | TC IDs | Exec | Evidence | Status | Owner | Updated | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| FR-021 | DFR-04-001 | SDS §6, OMB-01 §8 | TASK-P3-001, `models/workflow_instance.py` | TC-FR-021-001, TC-FR-021-002, TC-INT-runtime-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-02 | DFR-04-002 | SDS §6, OMB-01 §8 | TASK-P3-001, `models/workflow_instance.py` | TC-FR-022-001, TC-FR-022-002 | Auto | — | Not Run | QA | 2026-03-01 | Parallel gateway |
| FR-029 | — | SDS §6, OMB-01 §12 | TASK-P4-001, `models/workflow_task.py` | TC-FR-029-001 | Auto | — | Not Run | QA | 2026-03-01 | Cross-ref SRS-05 |

### 5.5 SRS-05 — Approver Resolution and Human Tasks

| Req ID | DFR Ref | Design Ref | Impl Ref | TC IDs | Exec | Evidence | Status | Owner | Updated | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| FR-029 | DFR-05-001 | SDS §6, OMB-01 §12 | TASK-P4-001, `models/workflow_task.py` | TC-FR-029-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-030 | DFR-05-002 | SDS §6, OMB-01 §12 | TASK-P4-001, `models/workflow_task.py` | TC-FR-030-001, TC-FR-030-002 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-031 | DFR-05-003 | SDS §4, OMB-01 §15 | TASK-P4-002, `models/workflow_approver_resolution.py` | TC-FR-031-001, TC-FR-031-002, TC-FR-031-003 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-032 | DFR-05-004 | SDS §6, OMB-01 §12 | TASK-P4-001, `models/workflow_task.py` | TC-FR-032-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-033 | DFR-05-005 | SDS §4, OMB-01 §14 | TASK-P4-003, `models/workflow_delegation_record.py` | TC-FR-033-001, TC-FR-033-002 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-034 | DFR-05-006 | SDS §6, OMB-01 §12 | TASK-P4-001, `models/workflow_task.py` | TC-FR-034-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-035 | DFR-05-007 | SDS §6, OMB-01 §12 | TASK-P4-001, `models/workflow_task.py` | TC-FR-035-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-047 | DFR-05-008 | SDS §4, OMB-01 §16 | TASK-P1-005, `models/workflow_follower_rule.py` | TC-FR-047-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-074 | DFR-05-009 | SDS §4, OMB-01 §15 | TASK-P4-002, `models/workflow_approver_resolution.py` | TC-FR-074-001 | Auto | — | Not Run | QA | 2026-03-01 | |

### 5.6 SRS-06 — Signature and Evidence

| Req ID | DFR Ref | Design Ref | Impl Ref | TC IDs | Exec | Evidence | Status | Owner | Updated | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| FR-043 | DFR-06-001 | SDS §13, OMB-01 §18 | TASK-P4-004, `models/workflow_signature_evidence.py` | TC-FR-043-001, TC-FR-043-002 | Auto | — | Blocked | QA | 2026-03-01 | OI-15: crypto baseline |
| FR-044 | DFR-06-002 | SDS §13, OMB-01 §18 | TASK-P4-004, `models/workflow_signature_evidence.py` | TC-FR-044-001 | Auto | — | Blocked | QA | 2026-03-01 | OI-15 |
| FR-045 | DFR-06-003 | SDS §13, OMB-01 §19 | TASK-P1-006, `models/workflow_attestation_policy.py` | TC-FR-045-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-046 | DFR-06-004 | SDS §13, OMB-01 §18 | TASK-P4-004, `models/workflow_signature_evidence.py` | TC-FR-046-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-084 | DFR-06-005 | SDS §13, OMB-01 §18 | TASK-P4-004, `models/workflow_signature_evidence.py` | TC-FR-084-001 | Auto | — | Blocked | QA | 2026-03-01 | OI-15 |
| FR-085 | DFR-06-006 | SDS §13, OMB-01 §18 | TASK-P4-004, `models/workflow_signature_evidence.py` | TC-FR-085-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-096 | DFR-06-007 | SDS §13, OMB-01 §18 | TASK-P4-004, `models/workflow_signature_evidence.py` | TC-FR-096-001, TC-FR-096-002 | Auto | — | Not Run | QA | 2026-03-01 | |

### 5.7 SRS-07 — Access, Security, Governance

| Req ID | DFR Ref | Design Ref | Impl Ref | TC IDs | Exec | Evidence | Status | Owner | Updated | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| FR-051 | DFR-07-001 | SDS §15, OMB-03 §3 | TASK-P1-008, `security/ir.model.access.csv` | TC-FR-051-001, TC-FR-051-002 | Auto | — | Not Run | Security | 2026-03-01 | |
| FR-052 | DFR-07-002 | SDS §11, OMB-01 §20 | TASK-P5-001, `models/workflow_access_grant.py` | TC-FR-052-001 | Auto | — | Not Run | Security | 2026-03-01 | |
| FR-053 | DFR-07-003 | SDS §11, OMB-01 §20 | TASK-P5-001, `models/workflow_access_grant.py` | TC-FR-053-001 | Auto | — | Not Run | Security | 2026-03-01 | |
| FR-054 | DFR-07-004 | SDS §11, OMB-01 §20 | TASK-P5-001, `models/workflow_access_grant.py` | TC-FR-054-001 | Auto | — | Not Run | Security | 2026-03-01 | |
| FR-055 | DFR-07-005 | SDS §11, OMB-01 §20 | TASK-P5-001, `models/workflow_access_grant.py` | TC-FR-055-001 | Auto | — | Not Run | Security | 2026-03-01 | |
| FR-061 | DFR-07-006 | SDS §15, OMB-03 §1 | TASK-P1-001, `security/workflow_security.xml` | TC-FR-061-001 | Auto | — | Not Run | Security | 2026-03-01 | Group hierarchy |
| FR-079 | DFR-07-007 | SDS §15, OMB-03 §2 | TASK-P1-008, `security/ir.model.access.csv` | TC-FR-079-001, TC-FR-079-002, TC-INT-security-001 | Auto | — | Not Run | Security | 2026-03-01 | |
| FR-080 | DFR-07-008 | SDS §15, OMB-03 §3 | TASK-P3-006, `security/ir.model.access.csv` | TC-FR-080-001 | Auto | — | Not Run | Security | 2026-03-01 | |

### 5.8 SRS-08 — Notifications, Webhooks, External Contracts

| Req ID | DFR Ref | Design Ref | Impl Ref | TC IDs | Exec | Evidence | Status | Owner | Updated | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| FR-056 | DFR-08-001 | SDS §12, OMB-01 §24 | TASK-P5-003, `models/workflow_webhook_endpoint.py` | TC-FR-056-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-057 | DFR-08-002 | SDS §12, OMB-01 §25 | TASK-P5-003, `models/workflow_outbound_event.py` | TC-FR-057-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-058 | DFR-08-003 | SDS §12, OMB-01 §25 | TASK-P5-003, `models/workflow_outbound_event.py` | TC-FR-058-001, TC-FR-058-002 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-059 | DFR-08-004 | SDS §12, OMB-01 §25 | TASK-P5-003, `models/workflow_outbound_event.py` | TC-FR-059-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-060 | DFR-08-005 | SDS §12, OMB-01 §22 | TASK-P5-002, `models/workflow_notification_template.py` | TC-FR-060-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| FR-083 | DFR-08-006 | SDS §12, OMB-01 §25 | TASK-P5-003, `models/workflow_outbound_event.py` | TC-FR-083-001 | Auto | — | Not Run | QA | 2026-03-01 | |

### 5.9 SRS-09 — Operations, Monitoring, Retention

| Req ID | DFR Ref | Design Ref | Impl Ref | TC IDs | Exec | Evidence | Status | Owner | Updated | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| FR-067 | DFR-09-001 | SDS §14, OMB-06 §5 | TASK-P6-003, `views/workflow_operations_dashboard.xml` | TC-FR-067-001, TC-FR-067-002 | Manual+Auto | — | Not Run | Ops | 2026-03-01 | |
| FR-068 | DFR-09-002 | SDS §14, OMB-06 §2 | TASK-P6-001, `models/workflow_archive_job.py` | TC-FR-068-001 | Auto | — | Not Run | Ops | 2026-03-01 | |
| FR-069 | DFR-09-003 | SDS §14, OMB-06 §2 | TASK-P6-001, `models/workflow_archive_job.py` | TC-FR-069-001 | Auto | — | Not Run | Ops | 2026-03-01 | |
| FR-070 | DFR-09-004 | SDS §14, OMB-06 §3 | TASK-P6-002, `wizards/workflow_purge_wizard.py` | TC-FR-070-001 | Manual | — | Not Run | Ops | 2026-03-01 | |
| FR-076 | DFR-09-005 | SDS §14, OMB-06 §1 | TASK-P6-001, `models/workflow_retention_policy.py` | TC-FR-076-001, TC-FR-076-002 | Auto | — | Not Run | Ops | 2026-03-01 | |
| FR-077 | DFR-09-006 | SDS §14, OMB-06 §3 | TASK-P6-002, `wizards/workflow_purge_wizard.py` | TC-FR-077-001 | Auto | — | Not Run | Ops | 2026-03-01 | |

### 5.10 NFR Requirements

| Req ID | DFR Ref | Design Ref | Impl Ref | TC IDs | Exec | Evidence | Status | Owner | Updated | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| NFR-001 | — | SDS §14, TVS §5.5 | TASK-P6-009, `tests/test_integration_e2e.py` | TC-NFR-001-001 | Auto+Manual | — | Not Run | Ops | 2026-03-01 | |
| NFR-002 | — | SDS §6, TVS §5.5 | TASK-P3-012, `tests/test_workflow_runtime.py` | TC-NFR-002-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| NFR-003 | — | SDS §14, TVS §5.5 | TASK-P6-009, `tests/test_integration_e2e.py` | TC-NFR-003-001 | Auto | — | Not Run | Ops | 2026-03-01 | |
| NFR-004 | — | SDS §7, TVS §5.5 | TASK-P2-010, `tests/test_workflow_enforcement.py` | TC-NFR-004-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| NFR-005 | — | SDS §12, TVS §5.5 | TASK-P5-007, `tests/test_workflow_security.py` | TC-NFR-005-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| NFR-006 | — | SDS §14, TVS §5.5 | TASK-P6-008, `tests/test_retention.py` | TC-NFR-006-001 | Auto | — | Not Run | Ops | 2026-03-01 | |
| NFR-007 | — | SDS §15, TVS §5.5 | TASK-P5-007, `tests/test_workflow_security.py` | TC-NFR-007-001 | Auto+Manual | — | Not Run | Security | 2026-03-01 | |
| NFR-008 | — | SDS §4, TVS §5.5 | TASK-P1-010, `tests/test_workflow_definition.py` | TC-NFR-008-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| NFR-009 | — | SDS §5, TVS §5.5 | TASK-P3-008, `static/src/components/bpmn_modeler/` | TC-NFR-009-001 | Manual | — | Not Run | QA | 2026-03-01 | |
| NFR-010 | — | SDS §6, TVS §5.5 | TASK-P5-007, `tests/test_workflow_security.py` | TC-NFR-010-001 | Auto | — | Not Run | Security | 2026-03-01 | |
| NFR-011 | — | SDS §5, TVS §5.5 | TASK-P3-010, `static/src/fields/bpmn_field.js` | TC-NFR-011-001 | Manual | — | Not Run | QA | 2026-03-01 | |
| NFR-012 | — | SDS §15, TVS §5.5 | TASK-P5-007, `tests/test_workflow_security.py` | TC-NFR-012-001 | Auto | — | Not Run | Security | 2026-03-01 | |
| NFR-013 | — | SDS §14, TVS §5.5 | TASK-P6-008, `tests/test_archival.py` | TC-NFR-013-001 | Manual+Auto | — | Not Run | Ops | 2026-03-01 | |
| NFR-014 | — | SDS §16, TVS §5.5 | TASK-P4-005, `views/workflow_task_views.xml` | TC-NFR-014-001 | Manual | — | Not Run | QA | 2026-03-01 | |
| NFR-015 | — | SDS §16, TVS §5.5 | TASK-P6-005, `readme/` | TC-NFR-015-001 | Auto | — | Not Run | QA | 2026-03-01 | |
| NFR-016 | — | SDS §10, OMB-01 §26 | TASK-P5-004, `models/workflow_idempotency_registry.py` | TC-NFR-016-001, TC-NFR-016-002, TC-NFR-016-003 | Auto | — | Not Run | QA | 2026-03-01 | OI-23 |
| NFR-017 | — | SDS §7, TVS §5.5 | TASK-P2-002, `models/workflow_enforcement_interceptor.py` | TC-NFR-017-001 | Auto | — | Not Run | QA | 2026-03-01 | |

---

## 6. Completion Backlog

1. ~~Expand matrix from seeded rows to all in-scope `FR-*` and `NFR-*`.~~ ✅ Done (v1.0)
2. ~~Replace all `TBD-SRSxx` tags with exact `DFR-*` IDs from child SRS docs.~~ ✅ Done (v1.0)
3. ~~Replace `TASK-P*-*` placeholders with actual `TASK-*` IDs from ITM.~~ ✅ Done (v1.0)
4. Replace `—` evidence fields with CI links or artifact paths. (At execution time)
5. Resolve all `Blocked` rows or provide approved waivers. (OI-15, OI-23)

## 7. Sign-off

| Role | Name | Date | Approval |
|---|---|---|---|
| QA Lead | | | |
| Tech Lead | | | |
| Product Owner | | | |
| Security Lead | | | |
