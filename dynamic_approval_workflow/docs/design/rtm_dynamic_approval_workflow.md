# Requirements-to-Test Matrix (RTM) — Dynamic Approval Workflow

Version: `v0.1-draft`  
Date: `2026-03-01`  
Owner: `QA Lead`  
Status: `seeded`

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

## 5. Seed Matrix (Critical Path First)

| Requirement ID | DFR Reference | Design Reference | Implementation Reference | Test Case IDs | Execution Type | Last Run Evidence | Status | Owner | Updated At | Notes |
|---|---|---|---|---|---|---|---|---|---|---|
| FR-001 | `TBD-SRS01` | `SDS: module/inheritance`, `OMB: model specs` | `TASK-P1-*`, `models/workflow_definition.py` | `TC-FR-001-001`, `TC-FR-001-002` | Automated | `TBD` | Not Run | QA Lead | 2026-03-01 | Workflow creation from UI |
| FR-007 | `TBD-SRS02` | `SDS: ORM interceptor`, `OMB: binding model` | `TASK-P2-*`, `models/workflow_binding.py` | `TC-FR-007-001` | Automated | `TBD` | Not Run | QA Lead | 2026-03-01 | Binding by model/action |
| FR-013 | `TBD-SRS03` | `SDS: BPMN integration`, `OMB: OWL specs` | `TASK-P3-*`, `static/src/components/*` | `TC-FR-013-001` | Manual + Automated | `TBD` | Not Run | QA Lead | 2026-03-01 | BPMN modeler availability |
| FR-021 | `TBD-SRS04` | `SDS: runtime engine`, `OMB: runtime models` | `TASK-P3-*`, `models/workflow_instance.py` | `TC-FR-021-001`, `TC-INT-runtime-001` | Automated | `TBD` | Not Run | QA Lead | 2026-03-01 | Runtime token progression |
| FR-029 | `TBD-SRS05` | `SDS: task resolution`, `OMB: task model` | `TASK-P4-*`, `models/workflow_task.py` | `TC-FR-029-001` | Automated | `TBD` | Not Run | QA Lead | 2026-03-01 | Human task assignment |
| FR-043 | `TBD-SRS06` | `SDS: evidence storage`, `OMB: signature model` | `TASK-P4-*`, `models/workflow_signature_evidence.py` | `TC-FR-043-001` | Automated | `TBD` | Blocked | QA Lead | 2026-03-01 | Blocked by crypto baseline decision |
| FR-051 | `TBD-SRS07` | `SDS: multi-company isolation`, `OMB: security` | `TASK-P1-*`, `security/*.xml` | `TC-FR-051-001`, `TC-INT-security-001` | Automated | `TBD` | Not Run | QA Lead | 2026-03-01 | Role and access boundaries |
| FR-056 | `TBD-SRS08` | `SDS: webhook architecture`, `OMB: outbound events` | `TASK-P5-*`, `models/workflow_outbound_event.py` | `TC-FR-056-001` | Automated | `TBD` | Not Run | QA Lead | 2026-03-01 | Notification/webhook dispatch |
| FR-067 | `TBD-SRS09` | `SDS: operations pattern`, `OMB: dashboard views` | `TASK-P6-*`, `views/workflow_dashboard.xml` | `TC-FR-067-001` | Manual + Automated | `TBD` | Not Run | QA Lead | 2026-03-01 | Ops dashboard counts/drill-down |
| FR-076 | `TBD-SRS09` | `SDS: retention/archival`, `OMB: retention policy model` | `TASK-P6-*`, `models/workflow_archive_job.py` | `TC-FR-076-001`, `TC-INT-retention-001` | Automated | `TBD` | Not Run | QA Lead | 2026-03-01 | Archival and purge policy |
| FR-079 | `TBD-SRS07` | `SDS: multi-company isolation`, `OMB: record rules` | `TASK-P1-*`, `security/ir_rule*.xml` | `TC-FR-079-001`, `TC-FR-079-002` | Automated | `TBD` | Not Run | QA Lead | 2026-03-01 | Isolation across all queries/tasks |
| FR-083 | `TBD-SRS08` | `SDS: external integration`, `OMB: webhook schema` | `TASK-P5-*`, `models/workflow_webhook_event.py` | `TC-FR-083-001` | Automated | `TBD` | Not Run | QA Lead | 2026-03-01 | External contract behavior |
| FR-090 | `TBD-SRS02` | `SDS: callback strategy`, `OMB: callback fields` | `TASK-P2-*`, `models/workflow_binding.py` | `TC-FR-090-001` | Automated | `TBD` | Not Run | QA Lead | 2026-03-01 | Extended binding/control behavior |
| FR-096 | `TBD-SRS06` | `SDS: attestation/evidence`, `OMB: evidence metadata` | `TASK-P4-*`, `models/workflow_signature_evidence.py` | `TC-FR-096-001` | Automated | `TBD` | Blocked | QA Lead | 2026-03-01 | Depends on signature policy finalization |
| NFR-001 | `TBD-SRS09` | `SDS: reliability`, `TVS: non-functional` | `TASK-P6-*`, `tests/perf/*` | `TC-NFR-001-001` | Automated + Manual | `TBD` | Not Run | Ops Lead | 2026-03-01 | Availability validation evidence |
| NFR-005 | `TBD-SRS08` | `SDS: webhook retries`, `OMB: retry fields` | `TASK-P5-*`, `models/workflow_outbound_event.py` | `TC-NFR-005-001` | Automated | `TBD` | Not Run | QA Lead | 2026-03-01 | Delivery reliability behavior |
| NFR-007 | `TBD-SRS07` | `SDS: security controls`, `OMB: ACL/rules` | `TASK-P1-*`, `security/*` | `TC-NFR-007-001` | Automated + Manual | `TBD` | Not Run | Security Lead | 2026-03-01 | Security control effectiveness |
| NFR-010 | `TBD-SRS07` | `SDS: governance/audit`, `OMB: audit models` | `TASK-P5-*`, `models/workflow_audit_event.py` | `TC-NFR-010-001` | Automated | `TBD` | Not Run | Security Lead | 2026-03-01 | Governance and traceability controls |
| NFR-013 | `TBD-SRS09` | `SDS: backup/restore constraints`, `TVS: env strategy` | `TASK-P6-*`, `ops runbooks` | `TC-NFR-013-001` | Manual + Automated | `TBD` | Not Run | Ops Lead | 2026-03-01 | RPO/RTO evidence |
| NFR-016 | `TBD-SRS10` | `SDS: data contract`, `OMB: API/event schema` | `TASK-P6-*`, `tests/contracts/*` | `TC-NFR-016-001` | Automated | `TBD` | Not Run | QA Lead | 2026-03-01 | Contract and schema governance |

## 6. Completion Backlog

The following actions must be completed before release:

1. Expand matrix from seeded rows to all in-scope `FR-*` and `NFR-*`.
2. Replace all `TBD-SRSxx` tags with exact `DFR-*` IDs from child SRS docs.
3. Replace `TASK-P*-*` placeholders with actual `TASK-*` IDs from ITM.
4. Replace `TBD` evidence fields with CI links or artifact paths.
5. Resolve all `Blocked` rows or provide approved waivers.

## 7. Sign-off

| Role | Name | Date | Approval |
|---|---|---|---|
| QA Lead | | | |
| Tech Lead | | | |
| Product Owner | | | |
| Security Lead | | | |
