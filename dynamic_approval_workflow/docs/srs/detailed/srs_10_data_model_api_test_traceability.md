# SRS-10 Data Model, API Contract, and Test Traceability

Version: `v1.2-draft`
Date: `2026-03-01`
Parent: `dynamic_approval_workflow_srs_v1.3.md`
Master Traceability: `srs_00_master_traceability.md`

## 1. Purpose
Define cross-cutting contracts for canonical data entities, runtime adapter APIs, idempotent mutation semantics, event schema governance, and requirement-to-test traceability execution.

## 2. Scope
In scope:
1. Conceptual-to-logical data model mapping for workflow core objects.
2. Runtime adapter contract details and mutation semantics.
3. Idempotency and correlation model for mutating operations.
4. Event payload schema versioning and compatibility policy.
5. Traceability reporting contract for FR/NFR to test evidence.

Out of scope:
1. Business behavior specifics already owned by SRS-01..SRS-09.
2. UI/UX wireframe-level design details.

## 3. Inherited Requirement Coverage
- NFR: `NFR-016` (primary ownership)
- Contract references: `FR-058..060`, `FR-068..070` (cross-cutting interface alignment)
- Contract sections: Parent SRS sections `8`, `9`, `12`, `15`

## 4. Decomposed Detailed Requirements (DFR)
| DFR ID | Statement | Maps To |
|---|---|---|
| `DFR-10-001` | Runtime adapter mutating operations shall be effectively-once under at-least-once delivery when valid `idempotency_key` is supplied (see portfolio glossary for term definition). | `NFR-016` |
| `DFR-10-002` | Duplicate mutating calls with same idempotency key and operation scope shall return stable original outcome and correlation reference without duplicate side effects. | `NFR-016` |
| `DFR-10-003` | Same idempotency key with conflicting payload shall be rejected with deterministic conflict response. | `NFR-016` |
| `DFR-10-004a` | Webhook event schemas shall be versioned with explicit `schema_version`, backward-compatible minor additions, and breaking-change major version with migration notice. | `FR-058`, `FR-060` |
| `DFR-10-004b` | Webhook retry and dead-letter event schemas shall maintain version alignment with delivery contract and include attempt metadata. | `FR-059` |
| `DFR-10-004c` | Incident queue and recovery API schemas shall be versioned and include structured error categories with deterministic recovery action references. | `FR-068` |
| `DFR-10-004d` | Per-record trace and observability API schemas shall include correlation IDs and support backward-compatible extension. | `FR-069`, `FR-070` |
| `DFR-10-005` | Requirement-to-test traceability export shall provide machine-readable mapping, execution evidence, and coverage completeness status. | `NFR-016` (governance support) |

## 5. Domain Objects (Conceptual-to-Logical Mapping)
| Conceptual Object | Logical Contract Key Fields |
|---|---|
| `workflow.definition` | `id`, `key`, `owner_company_id`, `status` |
| `workflow.definition.version` | `definition_id`, `version`, `bpmn_hash`, `published_at_utc` |
| `workflow.binding` | `id`, `model`, `action_key`, `enforcement_mode`, `rollout_scope` |
| `workflow.instance` | `id`, `definition_key`, `definition_version`, `state`, `started_at`, `ended_at` |
| `workflow.task` | `id`, `instance_id`, `node_id`, `status`, `assignees`, `sla_due_at` |
| `workflow.audit.event` | `id`, `event_type`, `actor`, `occurred_at`, `object_ref`, `payload_hash` |
| `workflow.outbound.event` | `event_id`, `type`, `occurred_at`, `payload`, `signature` |
| `workflow.incident` | `id`, `category`, `severity`, `state`, `opened_at`, `resolved_at` |

## 6. Runtime Adapter Contract
### 6.1 Operations
1. `deploy(definition)`
2. `validate(definition)`
3. `start(binding_context, idempotency_key)`
4. `signal(instance_id, signal_type, payload, idempotency_key, expected_instance_version=None)`
5. `complete_task(task_id, decision, payload, idempotency_key, expected_task_version=None)`
6. `cancel_instance(instance_id, reason, idempotency_key)`
7. `reassign_task(task_id, assignee_ref, reason, idempotency_key)`
8. `execute_post_approval_callback(instance_id, callback_ref, idempotency_key)`
9. `get_instance_state(instance_id)`
10. `get_gate_state(binding_context)`

### 6.2 Conflict and Version Semantics
1. Stale `expected_*_version` returns deterministic conflict without mutation.
2. Conflict response includes object reference and latest known version token.
3. Read operations must not alter mutation idempotency state.

## 7. Idempotency and Correlation Model
### 7.1 Idempotency Key Scope
1. Key uniqueness scope is `(operation_type, operation_subject_ref, idempotency_key)`.
2. Same key reused for different operation scope is invalid.

### 7.2 Outcome Registry
1. Every accepted mutation writes idempotency outcome record.
2. Duplicate request with same scope returns original status/result reference.
3. Conflicting payload with same key returns `idempotency_conflict`.

### 7.3 Correlation Fields
1. `correlation_id`
2. `causation_id`
3. `operation_scope_hash`
4. `idempotency_key`

## 8. Event Schema and Evolution Policy
### 8.1 Versioning Rules
1. Every external event schema has explicit `schema_version`.
2. Backward-compatible additions allowed in minor version.
3. Breaking changes require major version and migration notice.

### 8.2 Canonical Serialization Rules
1. Canonical JSON serialization policy must be deterministic.
2. Signature generation/verification uses canonical payload representation.

### 8.3 Deprecation Workflow
1. Deprecation notice period required before removing schema fields.
2. Deprecated fields remain documented until end-of-support date.

## 9. Traceability Reporting Contract
### 9.1 Required Artifacts
1. Requirement-to-test mapping export.
2. Test execution evidence report by requirement ID.
3. Uncovered requirement report with severity classification.

### 9.2 Completeness Rules
1. Every owned canonical requirement must map to at least one test.
2. Compliance/security requirements require positive and negative tests.
3. Release readiness blocked if uncovered critical requirement exists.

### 9.3 Machine-Readable Export
1. JSON export with requirement IDs, test IDs, status, run timestamp, and evidence links.
2. Stable schema for CI ingestion.

## 10. APIs and Events (Contract Governance)
### 10.1 Logical Operations
1. `register_idempotency_outcome(operation_scope, idempotency_key, result_ref)`
2. `resolve_idempotency_outcome(operation_scope, idempotency_key)`
3. `validate_event_schema(event_type, schema_version, payload)`
4. `publish_traceability_report(release_id)`
5. `query_requirement_coverage(requirement_id)`

### 10.2 Required Audit Events
1. `workflow.contract.idempotency_registered`
2. `workflow.contract.idempotency_replayed`
3. `workflow.contract.idempotency_conflict`
4. `workflow.contract.schema_validation_failed`
5. `workflow.contract.traceability_report_published`

## 11. Acceptance Criteria and Test Scenarios
| Test ID | Requirement IDs | Scenario | Expected Result |
|---|---|---|---|
| `TC-NFR-016-001` | `NFR-016` | Duplicate mutating call with same key/scope | Original outcome returned; no duplicate side effect |
| `TC-NFR-016-002` | `NFR-016` | Same key reused with conflicting payload | Deterministic `idempotency_conflict` response |
| `TC-NFR-016-003` | `NFR-016` | At-least-once delivery retries under transient network faults | Effectively-once mutation guarantee preserved |
| `TC-X-10-001a` | `FR-058`, `FR-060` | Validate webhook event schema version compatibility | Schema follows versioning rules; backward-compatible |
| `TC-X-10-001b` | `FR-059` | Validate retry/DLQ event schema version alignment | Schema includes attempt metadata and matches delivery contract |
| `TC-X-10-001c` | `FR-068` | Validate incident recovery API schema | Structured error categories and recovery actions present |
| `TC-X-10-001d` | `FR-069`, `FR-070` | Validate trace/observability API schema | Correlation IDs present; backward extension compatible |
| `TC-X-10-002` | `NFR-016` | Publish machine-readable traceability report for release | Coverage export generated with stable schema |
| `TC-X-10-003` | `NFR-016`, `FR-068` | Replay recovery action with preserved idempotency scope | Recovery path remains side-effect safe |
| `TC-NFR-016-004` | `NFR-016` | Idempotency key reused after retention window expiry | Rejected or treated as new per retention policy |
| `TC-NFR-016-005` | `NFR-016` | Partial write before idempotency registry commit | Transaction rollback; no visible mutation |
| `TC-X-10-004` | `FR-058`, `FR-068` | Schema version mismatch during consumer rollout | Validation failure signaled; no silent corruption |

## 12. Traceability Matrix
| Canonical ID / Contract Ref | Covered Sections | Primary Tests |
|---|---|---|
| `NFR-016` | 4, 6, 7, 9 | `TC-NFR-016-001`, `TC-NFR-016-002`, `TC-NFR-016-003`, `TC-X-10-002` |
| `FR-058` | 4, 8 | `TC-X-10-001a` |
| `FR-059` | 4, 8 | `TC-X-10-001b` |
| `FR-060` | 4, 8 | `TC-X-10-001a` |
| `FR-068` | 4, 9 | `TC-X-10-001c`, `TC-X-10-003` |
| `FR-069` | 4, 9 | `TC-X-10-001d` |
| `FR-070` | 4, 9 | `TC-X-10-001d` |

## 13. Edge Case Register
| Edge Case ID | Edge Case | Expected Behavior | Owner | Linked Test ID |
|---|---|---|---|---|
| `EC-10-01` | Same idempotency key reused after retention window expiry | Request rejected or treated as new only if retention policy permits and contract documents cutoff | Tech Lead | `TC-NFR-016-004` |
| `EC-10-02` | Partial write before idempotency registry commit | Transaction rollback/no-visible mutation guarantee | DBA Lead | `TC-NFR-016-005` |
| `EC-10-03` | Schema version mismatch during consumer rollout | Producer/consumer contract signals validation failure without silent corruption | Integration Lead | `TC-X-10-004` |

## 14. Sign-off Checklist
1. NFR-016 semantics are deterministic and decision-complete.
2. Adapter conflict/version behavior is explicitly defined.
3. Schema versioning/deprecation workflow is documented.
4. Traceability export requirements are machine-readable and CI-compatible.
5. Cross-SRS contract references are consistent with SRS-08 and SRS-09.

## 15. Open Issues
1. Idempotency retention-window duration requires final data-retention policy alignment.
2. Traceability export schema versioning policy requires QA tooling integration sign-off.

## 16. Next Document
After approval of `SRS-10`, run full-portfolio consistency review (`review_full_srs_connection.md`).
