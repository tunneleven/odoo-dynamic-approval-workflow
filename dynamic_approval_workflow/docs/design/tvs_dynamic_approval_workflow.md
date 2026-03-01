# Test & Validation Specification (TVS) — Dynamic Approval Workflow

Version: `v1.0`  
Date: `2026-03-01`  
Owner: `QA Lead`  
Status: `approved`

---

## 1. Purpose

Define the authoritative validation strategy for the `dynamic_approval_workflow` module, including:

1. What must be tested.
2. How tests are executed.
3. What evidence is required for release.
4. How requirements are proven through traceable test outcomes.

This document is the validation contract used with:

1. `SDS` (`docs/design/sds_dynamic_approval_workflow.md`)
2. `OMB` (`docs/design/omb_dynamic_approval_workflow.md`)
3. `ITM` (`docs/design/itm_dynamic_approval_workflow.md`)
4. `RTM` (`docs/design/rtm_dynamic_approval_workflow.md`)

## 2. Scope

### 2.1 In Scope

1. Functional behavior from SRS-01..SRS-10.
2. Non-functional validation for reliability, security, retention, and traceability.
3. Odoo backend tests, integration tests, and selected UI behavior validation.
4. Multi-company isolation and access-control verification.
5. Release evidence collection and sign-off criteria.

### 2.2 Out of Scope

1. Third-party infrastructure SLA verification outside module control.
2. Full browser compatibility matrix beyond agreed project targets.
3. Penetration testing executed by external security vendors.

## 3. Source References

1. `docs/srs/baseline/dynamic_approval_workflow_srs_v1.3.md`
2. `docs/srs/baseline/srs_00_master_traceability.md`
3. `docs/srs/detailed/srs_01_*` through `docs/srs/detailed/srs_10_*`
4. `docs/srs/supplementary/srs_to_development_bridge_plan.md`
5. Odoo 19 backend testing reference: `https://www.odoo.com/documentation/19.0/developer/reference/backend/testing.html`

## 4. Validation Objectives

Release quality is accepted only when all objectives are met:

1. All in-scope `FR-*` and `NFR-*` have mapped test coverage in RTM.
2. No unresolved severity `Critical` or `High` defects remain open.
3. Required automated suites pass in CI for release candidate branch.
4. Traceability chain is complete from requirement to evidence artifact.
5. Security, audit, and evidence policies satisfy compliance requirements.

## 5. Test Strategy

### 5.1 Test Levels

| Level | Purpose | Primary Technique | Owner |
|---|---|---|---|
| Unit | Validate model methods, constraints, utility functions | Odoo `TransactionCase` and targeted model assertions | Engineering |
| Integration | Validate cross-model workflow execution and side effects | Scenario tests with setup fixtures and action invocations | Engineering + QA |
| System | Validate end-to-end workflow lifecycle and user outcomes | Business-flow test scripts and smoke suite | QA |
| Regression | Prevent breakage in previously validated behavior | Curated baseline suite by risk tier | QA |
| Non-functional | Validate performance, reliability, retention, and security controls | Load probes, retention runs, and policy assertions | QA + Ops + Security |

### 5.2 Domain Coverage Strategy

| SRS Domain | Minimum Coverage Requirement |
|---|---|
| SRS-01 Definition/versioning | Publish lifecycle, version immutability, conflict handling |
| SRS-02 Binding/enforcement | Gate checks, callback behavior, interception failure paths |
| SRS-03 BPMN modeling/viewer | Model validation, diagram rendering, schema sanity checks |
| SRS-04 Runtime orchestration | Routing, parallel/quorum joins, timeout decisions, incidents |
| SRS-05 Human tasks | Assignment, delegation, reminders, resolution rules |
| SRS-06 Signature/evidence | Signature capture policy, evidence integrity, legal-hold behavior |
| SRS-07 Access/security | Role boundaries, record rules, multi-company isolation |
| SRS-08 Notifications/webhooks | Delivery flow, retry policy, webhook signature and schema |
| SRS-09 Operations/reliability | Dashboard metrics, archival/purge, backup/restore assertions |
| SRS-10 Data/API/traceability | Idempotency, contracts, test traceability completeness |

### 5.3 Test Design Rules

1. Each test case validates one primary behavior and may include bounded edge assertions.
2. Each critical requirement has positive, negative, and boundary coverage.
3. Compliance-critical requirements include explicit audit-log assertions.
4. Tests must be deterministic and isolated from non-required external systems.


### 5.4 Test Case Catalog by SRS Domain

This section defines concrete test scenarios organized by SRS domain. Each test case follows the TC-ID convention from §12 and is cross-referenced in the RTM.

#### 5.4.1 SRS-01 — Definition and Versioning (`FR-001..006`, `FR-066`, `FR-075`, `FR-086..089`)

| TC ID | Scenario | Type | Behavior |
|---|---|---|---|
| TC-FR-001-001 | Create workflow definition with valid data | Unit | Definition created, key auto-generated, state=draft |
| TC-FR-001-002 | Reject duplicate definition key within same company | Unit | ValidationError raised |
| TC-FR-002-001 | Create new version from published definition | Unit | Version number auto-incremented |
| TC-FR-002-002 | Publish version triggers immutability lock | Unit | Published version fields become read-only |
| TC-FR-003-001 | Archive published version | Unit | State transitions to archived, no longer resolves |
| TC-FR-003-002 | Prevent editing published version fields | Unit | UserError raised on write to locked fields |
| TC-FR-004-001 | Clone version creates new draft with incremented number | Unit | New version in draft, content copied |
| TC-FR-005-001 | Delete draft definition with no published versions | Unit | Definition and child records deleted |
| TC-FR-005-002 | Block deletion of definition with published versions | Unit | UserError raised |
| TC-FR-006-001 | Tag assignment and removal from definition | Unit | Many2many operations succeed |
| TC-FR-066-001 | Definition search by tag, key, and state filters | Unit | Search view filters return correct records |
| TC-FR-075-001 | Multi-company definition isolation | Integration | Company A cannot access Company B definitions |
| TC-FR-086-001 | Version history is preserved on publish | Unit | All prior versions remain accessible |

#### 5.4.2 SRS-02 — Binding, Enforcement, Callback (`FR-007..012`, `FR-071`, `FR-072`, `FR-081`, `FR-090..095`)

| TC ID | Scenario | Type | Behavior |
|---|---|---|---|
| TC-FR-007-001 | Create binding to target model | Unit | Binding created with correct model reference |
| TC-FR-007-002 | Binding scope unique per version constraint | Unit | Duplicate scope raises ValidationError |
| TC-FR-008-001 | Enforcement gate blocks write on bound model | Integration | Write raises GateBlockedError when no approval |
| TC-FR-008-002 | Enforcement gate allows write when approval active | Integration | Write succeeds with active approval instance |
| TC-FR-009-001 | Fail-closed: interceptor error returns block | Integration | Internal error in interceptor → operation blocked |
| TC-FR-010-001 | Enforcement covers all channels (UI, RPC, import, cron) | Integration | Gate fires for each channel type |
| TC-FR-011-001 | Callback fires on approval completion | Integration | Callback method invoked on target record |
| TC-FR-012-001 | Binding deactivation stops enforcement | Unit | Deactivated binding does not trigger gate |
| TC-FR-071-001 | Approval mixin adds computed fields to target | Integration | Target model shows approval_state, active instances |
| TC-FR-081-001 | Enforcement respects sudo() calls | Integration | Gate fires even under sudo context |
| TC-FR-090-001 | Callback with error creates incident | Integration | Callback exception → incident record created |

#### 5.4.3 SRS-03 — BPMN Modeling and Validation (`FR-013..020`)

| TC ID | Scenario | Type | Behavior |
|---|---|---|---|
| TC-FR-013-001 | BPMN modeler loads in form view | Manual | BpmnModeler OWL component renders without errors |
| TC-FR-013-002 | Diagram save triggers validation RPC | Manual | validate_bpmn_xml called on save |
| TC-FR-014-001 | Valid BPMN XML passes validation | Unit | No validation errors returned |
| TC-FR-014-002 | Invalid BPMN (missing end event) fails validation | Unit | Structured error with element reference |
| TC-FR-015-001 | Compile version creates compiled record | Unit | Compiled record with hash created |
| TC-FR-016-001 | BpmnViewer renders runtime state overlay | Manual | Nodes show state-based CSS colors |
| TC-FR-016-002 | Viewer polls runtime state at 5s interval | Manual | State updates reflect without page reload |
| TC-FR-017-001 | Diagram asset stores thumbnail | Unit | Thumbnail binary field populated |

#### 5.4.4 SRS-04 — Runtime Orchestration (`FR-021..028`, `FR-073`, `FR-082`)

| TC ID | Scenario | Type | Behavior |
|---|---|---|---|
| TC-FR-021-001 | Start workflow instance from published version | Integration | Instance created in started state, initial tokens placed |
| TC-FR-021-002 | Instance _tick advances tokens through sequence | Integration | Tokens move through sequential nodes |
| TC-FR-022-001 | Parallel gateway forks tokens correctly | Integration | N child tokens created at parallel split |
| TC-FR-022-002 | Parallel gateway joins with quorum | Integration | Merge fires after quorum threshold met |
| TC-FR-023-001 | Exclusive gateway evaluates conditions | Integration | Correct outward branch selected |
| TC-FR-023-002 | No matching condition raises incident | Integration | Incident created, instance state=error |
| TC-FR-025-001 | Token never deleted, only state transitions | Unit | Token states cycle, no unlink calls |
| TC-FR-026-001 | Advisory lock prevents concurrent _tick | Integration | Second _tick blocked by pg_advisory_xact_lock |
| TC-FR-027-001 | Cancel active instance | Integration | Instance cancelled, all tokens cancelled |
| TC-FR-028-001 | Recover errored instance | Integration | Instance state returns to resumable state |
| TC-FR-073-001 | Condition evaluation with safe_eval | Unit | safe_eval executes expression, returns boolean |
| TC-FR-082-001 | Timer boundary event triggers expiry | Integration | Expired timer advances token to timeout branch |
| TC-INT-runtime-001 | Full lifecycle: start → advance → complete | Integration | Instance transitions through all states to completed |

#### 5.4.5 SRS-05 — Approver Resolution and Human Tasks (`FR-029..042`, `FR-047..050`, `FR-074`)

| TC ID | Scenario | Type | Behavior |
|---|---|---|---|
| TC-FR-029-001 | Task created when node reaches approval step | Integration | Task record created with pending state |
| TC-FR-030-001 | Approve task transitions to completed | Unit | Task state=completed, transition logged |
| TC-FR-030-002 | Reject task transitions to cancelled | Unit | Task state=cancelled, reason recorded |
| TC-FR-031-001 | Resolve approvers from fixed user list | Unit | _resolve_approvers returns configured users |
| TC-FR-031-002 | Resolve approvers from group membership | Unit | _resolve_approvers returns group.users |
| TC-FR-031-003 | Resolve approvers from domain expression | Unit | _resolve_approvers evaluates domain, returns matches |
| TC-FR-032-001 | Reassign task to different user | Unit | Assignee changed, transition logged |
| TC-FR-033-001 | Delegate task within date range | Unit | Delegation active, delegate can act |
| TC-FR-033-002 | Expired delegation is inactive | Unit | _is_delegation_active returns False |
| TC-FR-034-001 | SLA deadline cron detects overdue task | Integration | Overdue task flagged, notification queued |
| TC-FR-035-001 | Deadline cron escalates task | Integration | Escalation action triggered |
| TC-FR-047-001 | Follower rule auto-subscribes users | Integration | Matching users added as followers |
| TC-FR-074-001 | No-approver fallback creates incident | Unit | Incident record with diagnostic info |

#### 5.4.6 SRS-06 — Signature and Evidence (`FR-043..046`, `FR-084`, `FR-085`, `FR-096`)

| TC ID | Scenario | Type | Behavior |
|---|---|---|---|
| TC-FR-043-001 | Create signature evidence with SHA-256 hash | Unit | Evidence created, hash computed |
| TC-FR-043-002 | Evidence immutability blocks write/unlink | Unit | UserError on write or unlink |
| TC-FR-044-001 | Supersede evidence creates new record | Unit | superseded_by_id set on original |
| TC-FR-045-001 | Attestation policy defines required evidence types | Unit | Policy fields populated, linked to version |
| TC-FR-046-001 | Evidence without matching policy raises error | Unit | ValidationError raised |
| TC-FR-084-001 | Evidence hash matches content on verification | Unit | Recomputed hash equals stored hash |
| TC-FR-085-001 | Evidence attachment stored correctly | Unit | Binary attachment accessible |
| TC-FR-096-001 | Evidence metadata includes capture timestamp | Unit | capture_timestamp not null |

#### 5.4.7 SRS-07 — Access, Security, Governance (`FR-051..055`, `FR-061..065`, `FR-079`)

| TC ID | Scenario | Type | Behavior |
|---|---|---|---|
| TC-FR-051-001 | ACL restricts model access by group | Unit | Unauthorized group cannot read/write |
| TC-FR-051-002 | Approver group can read tasks, not definitions | Unit | ACL rows correctly restrict per role |
| TC-FR-052-001 | Grant lifecycle: active → expired | Integration | _cron_expire_grants deactivates expired grants |
| TC-FR-053-001 | Grant lifecycle: active → revoked | Unit | Revocation immediate, logged |
| TC-FR-054-001 | Orphan grant reconciliation | Integration | _cron_reconcile removes orphaned grants |
| TC-FR-055-001 | Grant TTL enforcement (min/max bounds) | Unit | TTL outside 5min-72h raises ValidationError |
| TC-FR-079-001 | Multi-company record rule isolation | Integration | Company A user cannot see Company B records |
| TC-FR-079-002 | Multi-company isolation on workflow tasks | Integration | Task list filtered by company_id |
| TC-INT-security-001 | Full access boundary test across all models | Integration | Every runtime model enforces company scope |

#### 5.4.8 SRS-08 — Notifications, Webhooks, External Contracts (`FR-056..060`, `FR-083`)

| TC ID | Scenario | Type | Behavior |
|---|---|---|---|
| TC-FR-056-001 | Webhook endpoint stores HMAC secret | Unit | Secret field populated, not exposed |
| TC-FR-057-001 | Outbound event created on workflow trigger | Integration | Event record with queued state |
| TC-FR-058-001 | Event delivery with HMAC signature | Integration | HTTP header includes valid HMAC-SHA256 |
| TC-FR-058-002 | Failed delivery triggers retry with backoff | Integration | Retry count incremented, next_retry_at set |
| TC-FR-059-001 | Dead letter after max retries | Integration | Event state=dead_letter after 5 failures |
| TC-FR-060-001 | Notification template dispatches email | Integration | Mail queued via template |
| TC-FR-083-001 | RFC-8785 canonical JSON for signature | Unit | JSON output matches canonical form |

#### 5.4.9 SRS-09 — Operations, Monitoring, Retention (`FR-067..070`, `FR-076..078`)

| TC ID | Scenario | Type | Behavior |
|---|---|---|---|
| TC-FR-067-001 | Dashboard displays 4 stat cards | Manual + Auto | Counts match filtered model queries |
| TC-FR-067-002 | Dashboard drill-down opens filtered list | Manual | Click on card navigates to filtered list |
| TC-FR-068-001 | Archive job processes eligible instances | Integration | Completed instances archived per policy |
| TC-FR-069-001 | Legal hold blocks archival | Integration | Held instances excluded from archive job |
| TC-FR-070-001 | Purge wizard two-step confirmation | Manual | Purge requires explicit confirmation |
| TC-FR-076-001 | Retention profile eligibility logic | Unit | Profile selects correct age threshold |
| TC-FR-076-002 | Archive cron runs daily | Integration | Cron interval = 1 day, method callable |
| TC-FR-077-001 | Purge emits audit event | Integration | Audit log entry created on purge |
| TC-INT-retention-001 | Full archival lifecycle | Integration | Instance created → completed → archived → purged |

#### 5.4.10 SRS-10 — Data, API, Traceability (`FR-096`, `NFR-016`)

| TC ID | Scenario | Type | Behavior |
|---|---|---|---|
| TC-FR-096-002 | Evidence metadata schema compliance | Unit | All required metadata fields present |
| TC-NFR-016-001 | Idempotency registry detects replay | Unit | Same operation_scope_hash returns cached result |
| TC-NFR-016-002 | Idempotency registry detects conflict | Unit | Same hash + different payload raises IdempotencyError |
| TC-NFR-016-003 | Expired idempotency entries purged by cron | Integration | _cron_purge_expired removes old records |

### 5.5 Non-Functional Validation Thresholds

| NFR ID | Category | Pass Criteria | Test Method |
|---|---|---|---|
| NFR-001 | Availability | Module installs and starts without error on clean DB | Automated install test |
| NFR-002 | Runtime consistency | _tick processes 100 tokens in < 5s (single instance) | Load probe test |
| NFR-003 | Capacity | 1000 concurrent active instances without OOM | Stress fixture test |
| NFR-004 | Latency | Gate check completes in < 200ms per record | Timing assertion |
| NFR-005 | Integration reliability | Webhook retry delivers within 5 attempts or dead-letters | Retry scenario test |
| NFR-006 | Evidence retention | Archived data retrievable after retention window | Archive + query test |
| NFR-007 | Security isolation | Zero cross-company data leak across all runtime models | Exhaustive isolation suite |
| NFR-008 | Version stability | Published version content unchanged after 30-day aging | Hash comparison test |
| NFR-009 | UI integration | BPMN components render without JS console errors | Manual + eslint |
| NFR-010 | Governance | Every state transition creates audit event | Audit trail assertion |
| NFR-011 | Frontend compat | OWL components load in Odoo 19 web client | Manual smoke test |
| NFR-012 | Security controls | No ACL bypass via ORM API | Targeted access test |
| NFR-013 | Backup/restore | Module data survives pg_dump/pg_restore cycle | Backup restore test |
| NFR-014 | Mobile compat | Task approval works on mobile viewport | Manual responsive test |
| NFR-015 | Localization | All user-facing strings are translatable | _() wrapper check |
| NFR-016 | Idempotency | Replay and conflict detection work correctly | Unit test suite |
| NFR-017 | Cross-channel | Enforcement fires on UI, RPC, import, cron, sudo | Channel coverage test |

### 6.3 Data and Migration Test Strategy

#### 6.3.1 Module Install Idempotency

| Test | Method | Pass Criteria |
|---|---|---|
| Fresh install on empty DB | `odoo-bin -i dynamic_approval_core --stop-after-init` | Exit code 0, no errors |
| Reinstall (update) on existing | `odoo-bin -u dynamic_approval_core --stop-after-init` | Exit code 0, data preserved |
| Install all 3 modules together | `-i dynamic_approval_core,dynamic_approval_bpmn,dynamic_approval_operations` | No circular dependency errors |

#### 6.3.2 Demo Data Integrity

| Test | Method | Pass Criteria |
|---|---|---|
| Demo data loads without error | Install with `--dev=all` flag | All demo records created |
| Demo definitions are publishable | Action publish on demo version | State transitions to published |
| Two-company demo isolation | Query as each demo company user | Records correctly filtered |

#### 6.3.3 Upgrade Path

| Test | Method | Pass Criteria |
|---|---|---|
| v1.0 → v1.1 schema migration | Update module after data insertion | No data loss, new fields default |
| Cron jobs preserved after update | Check ir.cron after -u | All cron records intact |
| Security rules preserved | Check ir.rule after -u | All record rules active |
## 6. Environment and Data Strategy

### 6.1 Environment Matrix

| Environment | Purpose | Data Policy | Required for Sign-off |
|---|---|---|---|
| Local Dev | Fast iteration during implementation | Synthetic developer fixtures | No |
| CI | Mandatory automated gate | Seeded deterministic fixtures | Yes |
| Staging | Pre-release validation and smoke/UAT support | Production-like anonymized dataset | Yes |

### 6.2 Data Rules

1. Use deterministic fixture datasets for automated tests.
2. Cover at least two companies for isolation tests.
3. Include records triggering delegation, timeout, incident, and retention paths.
4. Do not use live personal data in test evidence.

## 7. Automation and Execution

### 7.1 Mandatory Command Stack

Run in this order for each merge candidate:

1. `python -m py_compile <changed_python_files>`
2. `odoo-bin -d <db> -i dynamic_approval_workflow --stop-after-init`
3. `odoo-bin -d <db> --test-tags /dynamic_approval_workflow`
4. `ruff check dynamic_approval_workflow`
5. `eslint dynamic_approval_workflow/static/src`
6. `pre-commit run --all-files` (if configured)

### 7.2 Automation Policy

| Test Type | Automation Requirement |
|---|---|
| Unit tests | Mandatory automated |
| Integration tests | Mandatory automated for critical flows |
| Regression smoke | Mandatory automated |
| UAT scenarios | Manual, with documented evidence |
| Exploratory tests | Manual, risk-driven |

## 8. Defect Management Policy

### 8.1 Severity Definitions

| Severity | Definition | Release Impact |
|---|---|---|
| Critical | Data corruption, security break, or workflow bypass | Blocks release |
| High | Major business flow failure with no acceptable workaround | Blocks release |
| Medium | Significant issue with controlled workaround | Allowed only with approved waiver |
| Low | Minor defect with limited business impact | Does not block release |

### 8.2 Triage Rules

1. Each failed critical-path test creates a tracked defect.
2. Waivers require owner, rationale, mitigation, and expiration date.
3. Reopened defects must retain historical evidence links.

## 9. Entry and Exit Criteria

### 9.1 Entry Criteria (Test Execution Start)

1. Relevant `TASK-*` implementations merged to test branch.
2. Required test data and environments are available.
3. RTM rows exist for in-scope requirements.

### 9.2 Exit Criteria (Release Recommendation)

1. RTM status for release scope is `Pass` or approved `Waived`.
2. No open `Critical` or `High` defects.
3. Mandatory automated suites pass on latest release candidate.
4. Evidence index is complete and reviewed.

## 10. Evidence and Reporting

### 10.1 Required Evidence Types

1. Automated test logs (CI links or archived logs).
2. Manual execution records for UAT and exploratory scenarios.
3. Defect reports and waiver approvals.
4. Final summary report per release candidate.

### 10.2 Evidence Storage

Primary index file:

1. `docs/design/test_evidence_index.md`

Recommended artifact directory structure:

1. `docs/design/evidence/<release_tag>/automated/`
2. `docs/design/evidence/<release_tag>/manual/`
3. `docs/design/evidence/<release_tag>/defects/`

## 11. RTM Integration Rules

1. Every in-scope `FR-*` and `NFR-*` must map to one or more `TC-*`.
2. Every `TC-*` must link to a concrete execution evidence record.
3. Every failed `TC-*` must link to a defect ID or approved waiver.
4. RTM status changes must include timestamp and owner.

## 12. Test Case ID Convention

Use stable identifiers:

1. `TC-FR-<id>-NNN` for functional requirements.
2. `TC-NFR-<id>-NNN` for non-functional requirements.
3. `TC-INT-<domain>-NNN` for cross-domain integration scenarios.
4. `TC-REG-<scope>-NNN` for regression suite cases.

## 13. Risks and Assumptions

1. Assumes completion of remaining SRS blockers before final release sign-off.
2. Assumes CI environment can run Odoo module tests consistently.
3. Assumes OMB and ITM remain authoritative and version-controlled.

## 14. Sign-off

| Role | Name | Date | Approval |
|---|---|---|---|
| QA Lead | | | |
| Tech Lead | | | |
| Security Lead | | | |
| Product Owner | | | |
