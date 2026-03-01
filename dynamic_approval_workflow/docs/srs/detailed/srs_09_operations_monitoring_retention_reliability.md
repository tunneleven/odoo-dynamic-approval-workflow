# SRS-09 Operations, Monitoring, Retention, and Reliability

Version: `v1.2-draft`
Date: `2026-03-01`
Parent: `dynamic_approval_workflow_srs_v1.3.md`
Master Traceability: `srs_00_master_traceability.md`

## 1. Purpose
Define detailed operational requirements for dashboards, incident handling, per-record observability trace, metrics/logs, retention archival/purge, mobile/responsive operations support, localization support, and reliability targets.

## 2. Scope
In scope:
1. Operations dashboards for active/overdue/failed/completed workflows.
2. Incident queue lifecycle and safe retry/recovery actions.
3. Per-record trace including timeline and diagram-state linkage.
4. Structured metrics and logs for observability.
5. Retention, archival, and purge policies.
6. Reliability targets: availability, capacity, backup/restore.
7. Mobile/responsive operational compatibility and localization behavior for workflow artifacts.

Out of scope:
1. Approver action semantics (`SRS-05`).
2. Webhook signature details (`SRS-08`).
3. Data schema definitions (`SRS-10`).

## 3. Inherited Requirement Coverage
- FR: `FR-067..070`, `FR-076..078`
- NFR: `NFR-001`, `NFR-003`, `NFR-013`, `NFR-015`

## 4. Decomposed Detailed Requirements (DFR)
| DFR ID | Statement | Maps To |
|---|---|---|
| `DFR-09-001` | Operations dashboard shall expose active, overdue, failed, and completed workflow counts and drill-downs. | `FR-067` |
| `DFR-09-002` | Incident queue shall support safe retry and controlled recovery actions with audit evidence. | `FR-068` |
| `DFR-09-003` | Per-record trace shall include event timeline and linked diagram-state context. | `FR-069` |
| `DFR-09-004` | Runtime observability shall expose structured metrics and logs with correlation IDs. | `FR-070` |
| `DFR-09-005` | Completed runtime data and logs shall support configurable archival and purge operations under retention policy. | `FR-076` |
| `DFR-09-006` | Operations interfaces for core task interactions shall remain responsive/mobile-compatible for supported form factors. | `FR-077` |
| `DFR-09-007` | Workflow labels, descriptions, notifications, and time rendering shall support localization and timezone-aware behavior. | `FR-078`, `NFR-015` |
| `DFR-09-008` | Runtime component availability target shall be 99.9% under defined scope boundary. | `NFR-001` |
| `DFR-09-009` | Capacity baseline shall support 1,000 approvals/24h, burst 4 approvals/min for 15 minutes, and 500 concurrent active instances. | `NFR-003` |
| `DFR-09-010` | Backup and restore capability shall satisfy RPO 15 minutes and RTO 60 minutes for workflow state. | `NFR-013` |

## 5. Domain Objects (Conceptual)
1. `workflow.ops_dashboard_snapshot`
- Aggregated operational counters and trend slices.
2. `workflow.incident_queue_item`
- Incident lifecycle record with recovery metadata.
3. `workflow.record_trace_view`
- Correlated timeline/diagram/task trace projection.
4. `workflow.metric_sample`
- Structured metric datapoint contract.
5. `workflow.retention_policy`
- Policy profile for archive/purge windows.
6. `workflow.backup_restore_run`
- Backup/restore operation evidence and SLA outcomes.

## 6. Dashboard and Observability Contract
### 6.1 Dashboard Metrics
1. Active workflows.
2. Overdue tasks/workflows.
3. Failed incidents pending action.
4. Completed workflows by period.

### 6.2 Drill-Downs
1. Filter by company, definition key, status, and time range.
2. Incident and trace drill-down linked to record-level context.

### 6.3 Structured Logging Contract
1. Every runtime transition and incident log includes correlation ID.
2. Logs include severity, component, event_type, object_ref, and timestamp.
3. PII masking policy is enforced for sensitive payload fields.

## 7. Incident Queue and Recovery Contract
### 7.1 Incident States
1. `open`
2. `triaged`
3. `retry_scheduled`
4. `resolved`
5. `closed_with_exception`

### 7.2 Safe Retry Rules
1. Retry action requires authorization and reason.
2. Retry must be idempotency-safe where mutation risk exists.
3. Retry execution result is captured in incident timeline.

### 7.3 Recovery Actions
1. `retry`
2. `skip_with_approval`
3. `manual_resolution_link`
4. `close_with_exception`

## 8. Per-Record Trace Contract
1. Trace view includes:
- workflow instance state transitions
- task transitions
- callback outcomes
- diagram-state references
- notification/webhook emissions
2. Trace query must be deterministic and audit-friendly.

## 9. Retention, Archival, and Purge Contract
### 9.1 Retention Profiles
| Profile | Retention Duration | Use Case |
|---|---|---|
| `short_term` | 90 days | Non-critical workflow runtime data, debug logs |
| `standard` | 365 days (1 year) | Default for completed instance data, task history, notification records |
| `compliance_extended` | 2,555 days (7 years) | Audit events, signature evidence, compliance-critical workflow records |

1. Durations are configurable per deployment; values above are mandatory defaults.
2. Legal-hold overrides all profile durations until hold is released.
3. Profile assignment is per-entity-type and per-binding `compliance_critical` flag.

### 9.2 Archival Rules
1. Only terminal/completed runtime records are archive candidates.
2. Archive must preserve audit linkage and evidence references.

### 9.3 Purge Rules
1. Purge is policy-driven and excludes legal-hold protected records.
2. Purge operations require approval and produce immutable purge report.

## 10. Reliability and Capacity Contract
### 10.1 Availability (`NFR-001`)
1. Target availability: 99.9% for runtime module components (engine, task services, webhook dispatcher).
2. Availability excludes full host-instance outages outside module control.

### 10.2 Capacity (`NFR-003`)
1. Baseline throughput: 1,000 approvals per rolling 24h window.
2. Burst: at least 4 approvals/minute sustained for 15 minutes.
3. Concurrency: at least 500 active instances.

### 10.3 Backup and Restore (`NFR-013`)
1. RPO <= 15 minutes.
2. RTO <= 60 minutes.
3. Backup/restore tests are run periodically and results auditable.

## 11. Mobile and Localization Operational Contract
### 11.1 Mobile Responsiveness (`FR-077`)
1. Core task interaction surfaces remain usable on supported mobile profile.
2. Operational dashboards provide responsive summary views for on-call users.

### 11.2 Localization and Timezone (`FR-078`, `NFR-015`)
1. Labels/descriptions/templates support i18n locale rendering.
2. All persisted timestamps are UTC; display layer is timezone-aware.
3. Trace and audit exports include UTC source values.

## 12. APIs and Events (Operations Domain)
### 12.1 Logical Operations
1. `get_ops_dashboard(filters)`
2. `list_incidents(filters)`
3. `execute_incident_recovery(incident_id, action, actor, reason)`
4. `get_record_trace(record_ref)`
5. `collect_metrics_snapshot(window)`
6. `run_archive_job(policy_profile)`
7. `run_purge_job(policy_profile, actor)`
8. `run_backup()`
9. `run_restore(validation_target)`

### 12.2 Required Audit Events
1. `workflow.ops.dashboard_viewed`
2. `workflow.ops.incident_recovery_executed`
3. `workflow.ops.trace_queried`
4. `workflow.ops.archive_completed`
5. `workflow.ops.purge_completed`
6. `workflow.ops.backup_completed`
7. `workflow.ops.restore_completed`
8. `workflow.ops.slo_breached`

## 13. Acceptance Criteria and Test Scenarios
| Test ID | Requirement IDs | Scenario | Expected Result |
|---|---|---|---|
| `TC-FR-067-001` | `FR-067` | Open operations dashboard | Active/overdue/failed/completed metrics shown |
| `TC-FR-068-001` | `FR-068` | Execute incident retry with authorization | Safe retry executed and audited |
| `TC-FR-068-002` | `FR-068` | Attempt unauthorized recovery action | Action rejected and logged |
| `TC-FR-069-001` | `FR-069` | Query per-record trace | Timeline + diagram-state linkage returned |
| `TC-FR-070-001` | `FR-070` | Emit runtime transitions under load | Structured logs/metrics with correlation IDs available |
| `TC-FR-076-001` | `FR-076` | Run archival job per retention policy | Eligible completed data archived |
| `TC-FR-076-002` | `FR-076` | Purge attempt on legal-hold record | Purge blocked with policy reason |
| `TC-FR-077-001` | `FR-077` | Core task interaction on mobile profile | Actions usable in responsive layout |
| `TC-FR-078-001` | `FR-078`, `NFR-015` | Render workflow artifacts in non-default locale/timezone | Correct localization/timezone rendering |
| `TC-NFR-001-001` | `NFR-001` | Measure availability over reporting window | 99.9% target met within defined scope |
| `TC-NFR-003-001` | `NFR-003` | Capacity test baseline + burst + concurrency | Throughput and concurrency targets met |
| `TC-NFR-013-001` | `NFR-013` | Backup and restore drill | RPO <= 15m and RTO <= 60m |
| `TC-NFR-015-001` | `NFR-015` | Export trace with timezone conversions | UTC source and localized display both correct |
| `TC-FR-068-003` | `FR-068`, `FR-070` | Repeated retries for same incident | Idempotent-safe retries with full audit trail |
| `TC-FR-068-004` | `FR-068` | Incident retry while original execution active | Retry blocked or serialized by idempotency guard |
| `TC-NFR-013-002` | `NFR-013` | Restore succeeds but stale metrics cache persists | Metrics cache invalidated before SLO reporting resumes |
| `TC-FR-078-002` | `FR-078`, `NFR-015` | Localization resource missing for selected language | Fallback locale applied; missing key warning logged |

## 14. Traceability Matrix
| Canonical ID | Covered Sections | Primary Tests |
|---|---|---|
| `FR-067` | 4, 6 | `TC-FR-067-001` |
| `FR-068` | 4, 7 | `TC-FR-068-001`, `TC-FR-068-002`, `TC-FR-068-003` |
| `FR-069` | 4, 8 | `TC-FR-069-001` |
| `FR-070` | 4, 6, 12 | `TC-FR-070-001`, `TC-FR-068-003` |
| `FR-076` | 4, 9 | `TC-FR-076-001`, `TC-FR-076-002` |
| `FR-077` | 4, 11 | `TC-FR-077-001` |
| `FR-078` | 4, 11 | `TC-FR-078-001` |
| `NFR-001` | 4, 10 | `TC-NFR-001-001` |
| `NFR-003` | 4, 10 | `TC-NFR-003-001` |
| `NFR-013` | 4, 10 | `TC-NFR-013-001` |
| `NFR-015` | 4, 11 | `TC-NFR-015-001`, `TC-FR-078-001` |

## 15. Edge Case Register
| Edge Case ID | Edge Case | Expected Behavior | Owner | Linked Test ID |
|---|---|---|---|---|
| `EC-09-01` | Incident retry triggered while original execution still active | Retry blocked or serialized by idempotency guard | Ops Lead | `TC-FR-068-004` |
| `EC-09-02` | Restore succeeds but stale metrics cache persists | Metrics cache invalidated before SLO reporting resumes | Tech Lead | `TC-NFR-013-002` |
| `EC-09-03` | Localization resource missing for selected language | Fallback locale applied and missing key warning logged | QA Lead | `TC-FR-078-002` |

## 16. Sign-off Checklist
1. All inherited requirements in Section 3 are mapped in Section 14.
2. Reliability targets include explicit numeric thresholds.
3. Incident recovery actions are authorization-protected and auditable.
4. Retention/archival/purge contracts include legal-hold safeguards.
5. Mobile and localization operational behavior is explicitly testable.

## 17. Open Issues
1. Final SLO alert thresholds and burn-rate alert formulas need SRE approval.
2. Localization fallback policy for custom customer templates requires product decision.

## 18. Next Document
After approval of `SRS-09`, proceed to `srs_10_data_model_api_test_traceability.md`.
