# SRS-01 Workflow Definition and Versioning

Version: `v1.2-draft`  
Date: `2026-02-27`  
Parent: `dynamic_approval_workflow_srs_v1.3.md`  
Master Traceability: `srs_00_master_traceability.md`

## 1. Purpose
Define detailed functional and non-functional requirements for workflow definition lifecycle, publication controls, activation precedence, rollback behavior, and draft edit concurrency.

## 2. Scope
In scope:
1. Definition creation, cloning, publishing, archiving, rollback activation.
2. Effective-date activation and deterministic version selection for new instances.
3. In-flight version pinning and stability controls.
4. Concurrency controls for draft editing.

Out of scope:
1. Runtime task execution semantics (covered by `SRS-04` and `SRS-05`).
2. Binding enforcement modes and callback execution (covered by `SRS-02`).

## 3. Inherited Requirement Coverage
- FR: `FR-001..006`, `FR-066`, `FR-075`, `FR-086..089`
- NFR: `NFR-008`

## 4. Decomposed Detailed Requirements (DFR)
| DFR ID | Statement | Maps To |
|---|---|---|
| `DFR-01-001` | The system shall create workflow definitions as `draft` objects via UI with no code deployment required. | `FR-001` |
| `DFR-01-002` | Definition lifecycle states shall be limited to `draft`, `published`, and `archived`, with explicit transition guards. | `FR-002` |
| `DFR-01-003` | Published definition versions shall be immutable in structure, policies, and compiled artifacts. | `FR-003` |
| `DFR-01-004` | Cloning a published or archived version shall produce a new draft with new draft metadata and link to source version. | `FR-004` |
| `DFR-01-005` | Publish action shall execute validation gates (schema, semantic, policy, activation window) and block publication on failure. | `FR-005` |
| `DFR-01-006` | Activation shall support explicit `effective_from_utc` and optional `effective_to_utc`. | `FR-006` |
| `DFR-01-007` | Rollback shall be represented as a new activation event to a prior published version, not mutation of historical versions. | `FR-066` |
| `DFR-01-008` | Draft edit collisions shall be detected through optimistic locking and resolved through an attributable merge/retry workflow. | `FR-075` |
| `DFR-01-009` | New-instance version resolution shall select active published version using deterministic precedence rules. | `FR-086`, `FR-089` |
| `DFR-01-010` | In-flight instances shall remain pinned to start-time version across activations and rollbacks. | `FR-087`, `NFR-008` |
| `DFR-01-011` | Rollback activation shall require explicit `effective_from_utc`, operator reason, and immutable audit events for activation and supersession. | `FR-088` |
| `DFR-01-012` | If no active published version exists for the start context and time window (including post-expiry gaps), new instance start shall be blocked with reason code and incident emission. | `FR-086` |

## 5. Domain Objects (Conceptual)
1. `workflow.definition`
- Stable definition key and ownership metadata.
2. `workflow.definition.version`
- Versioned record with lifecycle state and immutable publish payload.
3. `workflow.definition.edit.session`
- Draft edit lock/version token and conflict metadata.
4. `workflow.definition.activation_event`
- Activation or rollback event with reason, actor, and effective window.

### 5.1 Definition Key and Ownership Contract
1. `definition_key` is a human-readable slug (`[a-z0-9_]+`) scoped to a company owner.
2. Uniqueness scope is `(owner_company_id, definition_key)`.
3. Cardinality is `1 workflow.definition : N workflow.definition.version`.
4. `definition_key` may be edited only while no `published` version exists; after first publish it is immutable.
5. Required ownership metadata: `name`, `description`, `owner_company_id`, `created_by`, `created_at`, optional `tags[]`.

### 5.2 Version Numbering Contract
1. Published `version` number is assigned only at publish time.
2. Version numbering is monotonic increasing integer per `(owner_company_id, definition_key)`.
3. Draft records use `draft_id` plus optimistic-lock `revision`; draft revisions are not published version numbers.
4. Published version number is user-visible in audit, UI, and APIs.

## 6. Lifecycle State Machine
### 6.1 States
1. `draft`
- Editable, non-executable, not start-eligible.
2. `published`
- Immutable, executable when active by window/scope.
3. `archived`
- Non-editable, non-start-eligible, retained for audit.

### 6.2 Allowed Transitions and Operations
| Operation | Source State | Source State After | Created Record State | Actor | Preconditions | Result |
|---|---|---|---|---|---|---|
| Publish | `draft` | `published` | N/A | Workflow Designer/Admin | All publish validations pass | Immutable published version created |
| Archive | `published` | `archived` | N/A | Workflow Admin | Not currently configured as only active version for critical binding without successor | Source version archived |
| Clone | `published` | `published` | `draft` | Workflow Designer/Admin | Source version exists and is readable | New draft created; source remains published |
| Clone | `archived` | `archived` | `draft` | Workflow Designer/Admin | Source version exists and is readable | New draft created; source remains archived |
| Save edit | `draft` | `draft` | N/A | Workflow Designer/Admin | Valid optimistic lock token | Draft revision incremented |

Invalid transitions and unsupported operations shall be rejected with explicit reason code and audit event.

### 6.3 Invariants
1. A published version is immutable.
2. A draft version is never executable.
3. Archive operation never deletes audit history.
4. Clone operation never mutates the source version.

### 6.4 Deletion and Retention Boundary
1. Lifecycle states in this SRS are strictly `draft`, `published`, and `archived`.
2. User-facing delete operations for published/archived versions are out of scope and disallowed by this SRS.
3. Draft cleanup and physical purge are governed by retention controls in `SRS-09` (`workflow.retention.policy`, `workflow.archive.job`).
4. `workflow.definition` header cannot be hard-deleted while version or audit history exists.

### 6.5 Clone Field Rules
| Category | Fields | Rule |
|---|---|---|
| Copied | BPMN XML, step configs, approver rules, condition rules, policy fields | Copy from source version as baseline |
| Reset | `status`, `version`, `effective_from_utc`, `effective_to_utc`, compiled runtime cache | Set to draft defaults for new draft |
| Derived | `revision=1`, `cloned_from_version`, `cloned_by`, `cloned_at` | Set at clone execution |
| Not copied | Runtime instance bindings and runtime tokens | Re-created only by runtime start |

## 7. Publish Validation Contract
### 7.1 Validation Categories
1. Structural validation
- BPMN XML parseability and supported subset compliance (subset contract is defined by `SRS-03`).
2. Semantic validation
- Reachable end-state, gateway and join coherence, unresolved references check.
3. Policy validation
- Required governance fields, signature policy coherence, role constraints.
4. Activation validation
- Valid effective window and overlap policy checks in same resolution scope.
5. Compilation validation
- Compiled metadata generated and hash-linked to canonical XML using `SHA-256` over canonical BPMN bytes.

### 7.2 Publish Outcome
1. On success
- Create immutable published version artifact, assign publish version number, and emit publish audit event.
2. On failure
- Keep version as draft and return categorized validation errors.

### 7.3 Publish Idempotency and Retry
1. `publish_draft` supports `idempotency_key`.
2. Duplicate request with same key and same payload returns the same committed publish result.
3. Reuse of same key with different payload is rejected with `idempotency_conflict`.
4. If no key is provided, duplicate retries are prevented by state guards (`already_published`).

## 8. Activation and Precedence Rules
### 8.1 Activation Model
1. Activation is independent of publication timestamp.
2. Activation requires `effective_from_utc`; optional `effective_to_utc`.
3. Only `published` versions can be activated.

### 8.2 New Instance Version Resolution Algorithm
For a given instance start context `(definition_key, company, group/domain, start_time)`:
1. Filter candidate versions where:
- `status = published`
- scope matches binding context
- `effective_from_utc <= start_time < effective_to_utc` (or open-ended)
2. Order candidates by:
- highest rollout specificity (`company` > `group` > `global`)
- latest publish timestamp
- highest published version number (final deterministic tie-break)
3. If no candidate exists, block start with `reason_code = no_active_version` and raise incident.
4. If tie still remains after all precedence keys, block start and raise conflict incident.

### 8.3 Time Semantics
1. All evaluation uses UTC timestamps.
2. User-facing scheduling may use local timezone but must normalize to UTC before commit.

### 8.4 Overlap Validation Rules
1. Overlap checks run during publish validation and again at instance-start resolution.
2. "Same resolution scope" means same `(owner_company_id, definition_key, rollout_specificity, rollout_scope_value)`.
3. Time-window overlap is evaluated as half-open interval intersection.
4. Overlap across different specificity levels is legal shadowing by precedence (`company` > `group` > `global`).
5. Overlap that can produce unresolved ambiguity is rejected at publish; runtime still guards and incidents on residual conflicts.

### 8.5 Cross-SRS Boundary
1. Binding conflicts across different `definition_key` are owned by `SRS-02`.
2. This SRS resolves versions only within one `definition_key`.

## 9. Rollback as Activation Event
### 9.1 Rollback Rules
1. Rollback target must be an existing `published` version.
2. Rollback creates a new activation event with mandatory fields:
- target version
- `effective_from_utc`
- operator identity
- reason code
3. Rollback emits immutable audit events for activation and supersession.
4. Rollback does not modify historical records of superseded versions.

### 9.2 Rollback Safety
1. In-flight instances remain on their pinned version.
2. Only new instances after rollback effective time use rollback target version.
3. Rollback action emits activation and supersession audit events.

### 9.3 Rollback Idempotency and Retry
1. `rollback_activate` supports `idempotency_key`.
2. Duplicate request with same key and same payload returns same activation event.
3. Same key with different payload is rejected with `idempotency_conflict`.

## 10. Draft Concurrency and Conflict Handling
### 10.1 Optimistic Locking
1. Draft saves require current revision token.
2. If token mismatch occurs, save is rejected as conflict.

### 10.2 Conflict Workflow
1. Notify editor of conflict.
2. Provide comparison against latest draft revision.
3. Support merge/retry or discard local edits.
4. Record conflict event for audit.

### 10.3 Parallel Editor Policy
1. Multiple editors are allowed.
2. Last-write without token is disallowed.
3. Merge decisions must be attributable to actor and timestamp.

### 10.4 Merge Strategy (v1)
1. Compared artifacts are canonical BPMN XML and structured workflow metadata payload.
2. Auto-merge of BPMN XML is out of scope for v1.
3. Supported options are:
- discard local edits and reload latest draft
- overwrite latest draft with editor payload as a new revision
- manually reconcile in UI then save as a new revision
4. Partial field-level merge is not guaranteed in v1.
5. Every successful merge/retry decision emits `workflow.definition.merge_resolved`.

## 11. In-Flight Version Stability
1. Instance stores `definition_version` at start.
2. Runtime queries for that instance use stored version only.
3. Activation/rollback events must not mutate instance-version binding.
4. Migration to new version requires explicit future enhancement and is out of scope for this SRS.

## 12. APIs and Events (Definition Lifecycle)
### 12.1 Logical Operations
1. `create_draft(definition_key, owner_company_id, payload)`
2. `save_draft(draft_id, payload, expected_revision)`
3. `validate_draft(draft_id)`
4. `publish_draft(draft_id, effective_from_utc, effective_to_utc=None, idempotency_key=None)`
5. `clone_version(source_version_id)`
6. `archive_published(version_id)`
7. `rollback_activate(definition_key, target_version, effective_from_utc, reason_code, idempotency_key=None)`
8. `resolve_version(start_context)`

### 12.2 Required Audit Events
1. `workflow.definition.created`
2. `workflow.definition.validated`
3. `workflow.definition.published`
4. `workflow.definition.archived`
5. `workflow.definition.rollback_activated`
6. `workflow.definition.edit_conflict`
7. `workflow.definition.merge_resolved`
8. `workflow.definition.version_resolved`

### 12.3 Audit Payload Schema Ownership
1. Event payload schemas are owned by `SRS-10`.
2. Events listed in this SRS must have corresponding payload schema definitions in `SRS-10`.

## 13. Acceptance Criteria and Test Scenarios
| Test ID | Requirement IDs | Scenario | Expected Result |
|---|---|---|---|
| `TC-FR-001-001` | `FR-001` | Create new definition from UI | Draft created without code deployment |
| `TC-FR-001-002` | `FR-001` | Rename definition key after first publish exists | Rename rejected with state-precondition reason |
| `TC-FR-002-001` | `FR-002` | Attempt invalid lifecycle transition | Transition blocked with reason code |
| `TC-FR-002-002` | `FR-002`, `FR-006` | Attempt activation of non-published version | Request rejected; version state precondition enforced |
| `TC-FR-002-003` | `FR-002` | Archive request for sole active version on critical binding | Archive blocked by precondition and audit logged |
| `TC-FR-003-001` | `FR-003` | Attempt edit on published version | Edit denied; immutable guarantee preserved |
| `TC-FR-003-002` | `FR-003` | Attempt policy mutation on published version via API | Mutation denied; API-level immutability enforced |
| `TC-FR-004-001` | `FR-004` | Clone published version | New draft linked to source version |
| `TC-FR-004-002` | `FR-004` | Clone archived version | New draft created; source remains archived |
| `TC-FR-004-003` | `FR-004` | Verify clone copied/reset field rules | Copy/reset/derived rules match Section 6.5 |
| `TC-FR-005-001` | `FR-005` | Publish with failed validation | Publication blocked; categorized errors returned |
| `TC-FR-005-002` | `FR-005` | Publish with stale compiled artifact/hash mismatch | Publication blocked; integrity error returned |
| `TC-FR-005-003` | `FR-005` | Publish malformed BPMN XML | Publication blocked; structural error returned |
| `TC-FR-006-001` | `FR-006` | Publish with future effective date | Version becomes start-eligible only after effective time |
| `TC-FR-006-002` | `FR-006` | Backdated activation request | Policy applied (reject or elevated approval path) with audit |
| `TC-FR-066-001` | `FR-066` | Roll back to prior published version | New activation event created for prior version |
| `TC-FR-066-002` | `FR-066`, `FR-088` | Two rollback requests race on same definition and time window | Deterministic conflict handling; one activation committed; loser rejected |
| `TC-FR-066-003` | `FR-066` | Rollback to a version that was previously rollback target | Allowed; new activation event extends immutable chain |
| `TC-FR-066-004` | `FR-066` | Publish and rollback requested concurrently on same definition | Serialization/conflict control prevents ambiguous activation |
| `TC-FR-066-005` | `FR-066` | Duplicate retry on rollback/publish with same idempotency key | Same committed activation/publish event returned; no duplicate event |
| `TC-FR-075-001` | `FR-075` | Concurrent draft edits with stale token | Conflict returned; merge/retry flow triggered |
| `TC-FR-075-002` | `FR-075` | Same user edits same draft in two tabs with stale revision token | Conflict returned with merge/retry path |
| `TC-FR-075-003` | `FR-075` | Resolve conflict via merge workflow | New draft revision created and merge audit emitted |
| `TC-FR-086-001` | `FR-086` | Resolve active version for new instance | Deterministic active version selected |
| `TC-FR-086-002` | `FR-086` | `effective_to_utc` expires and no successor activation exists | New instance blocked with `no_active_version`; incident created |
| `TC-FR-086-003` | `FR-086` | Version resolution on new instance start | `workflow.definition.version_resolved` contains selected version and resolution inputs |
| `TC-FR-086-004` | `FR-086` | `start_time == effective_to_utc` boundary | Candidate is not active at exact boundary |
| `TC-FR-087-001` | `FR-087` | Activate new version while instance in-flight | In-flight instance remains on original version |
| `TC-FR-088-001` | `FR-088` | Execute rollback without reason/effective time | Request rejected as invalid |
| `TC-FR-088-002` | `FR-088` | Rollback target missing or not published | Request rejected; no activation event committed |
| `TC-FR-088-003` | `FR-088` | Activation/rollback audit write fails | Operation fails atomically; no partial commit |
| `TC-FR-089-001` | `FR-089` | Create unresolved overlapping activation tie | Instance start blocked; conflict incident created |
| `TC-NFR-008-001` | `NFR-008` | New version and rollback during active runtime | Existing instances remain stable and deterministic |
| `TC-NFR-008-002` | `NFR-008` | Clock skew near activation boundary across nodes | Resolution remains deterministic under UTC policy |

## 14. Traceability Matrix
| Canonical ID | Covered Sections | Primary Tests |
|---|---|---|
| `FR-001` | 4, 5, 12 | `TC-FR-001-001`, `TC-FR-001-002` |
| `FR-002` | 4, 6 | `TC-FR-002-001`, `TC-FR-002-002`, `TC-FR-002-003` |
| `FR-003` | 4, 6 | `TC-FR-003-001`, `TC-FR-003-002` |
| `FR-004` | 4, 6, 12 | `TC-FR-004-001`, `TC-FR-004-002`, `TC-FR-004-003` |
| `FR-005` | 4, 7 | `TC-FR-005-001`, `TC-FR-005-002`, `TC-FR-005-003` |
| `FR-006` | 4, 8 | `TC-FR-006-001`, `TC-FR-006-002` |
| `FR-066` | 4, 9, 12 | `TC-FR-066-001`, `TC-FR-066-002`, `TC-FR-066-004`, `TC-FR-066-005` |
| `FR-075` | 4, 10 | `TC-FR-075-001`, `TC-FR-075-002`, `TC-FR-075-003` |
| `FR-086` | 4, 8, 12 | `TC-FR-086-001`, `TC-FR-086-002`, `TC-FR-086-003`, `TC-FR-086-004` |
| `FR-087` | 4, 11 | `TC-FR-087-001` |
| `FR-088` | 4, 9, 12 | `TC-FR-088-001`, `TC-FR-088-002`, `TC-FR-088-003`, `TC-FR-066-002` |
| `FR-089` | 4, 8 | `TC-FR-089-001` |
| `NFR-008` | 4, 11 | `TC-NFR-008-001`, `TC-NFR-008-002` |

## 15. Edge Case Register
| Edge Case ID | Edge Case | Expected Behavior | Owner | Linked Test ID |
|---|---|---|---|---|
| `EC-01` | `start_time == effective_to_utc` boundary | Boundary is exclusive; candidate is not active at exact `effective_to_utc`. | Tech Lead | `TC-FR-086-004` |
| `EC-02` | Activation gap after `effective_to_utc` with no successor | Block new instance start with `no_active_version` and create incident. | Workflow Admin | `TC-FR-086-002` |
| `EC-03` | Overlap conflict with equal specificity | Deterministic tie-break; if unresolved tie remains, block and incident. | Tech Lead | `TC-FR-089-001` |
| `EC-04` | Concurrent publish and rollback on same definition | Conflict-safe serialization; one committed path, one rejected with conflict reason. | Tech Lead | `TC-FR-066-004` |
| `EC-05` | Activation attempt on non-published version | Reject with state precondition error. | Workflow Admin | `TC-FR-002-002` |
| `EC-06` | Rollback target version missing/not published | Reject rollback request; no activation event committed. | Workflow Admin | `TC-FR-088-002` |
| `EC-07` | Archive of sole active version for critical binding | Block archive by precondition and emit audit event. | Workflow Admin | `TC-FR-002-003` |
| `EC-08` | Same-user multi-tab stale draft revision | Optimistic-lock conflict; user must merge/retry. | Workflow Designer | `TC-FR-075-002` |
| `EC-09` | Publish with stale compiled artifact/hash mismatch | Reject publish and require recompilation. | Tech Lead | `TC-FR-005-002` |
| `EC-10` | Activation/rollback audit write failure | Fail operation atomically; no partial state commit without audit evidence. | Tech Lead | `TC-FR-088-003` |
| `EC-11` | Clock skew between nodes around activation times | Resolution must remain deterministic in UTC; skew tolerance policy enforced. | Ops Lead | `TC-NFR-008-002` |
| `EC-12` | Backdated activation/rollback effective time | Validate against policy; reject or require elevated approval according to governance. | Workflow Admin | `TC-FR-006-002` |
| `EC-13` | Definition key rename/migration during active lifecycle | Preserve stable key identity or block rename while active versions exist. | Tech Lead | `TC-FR-001-002` |
| `EC-14` | Duplicate retry on publish/rollback request | Idempotent handling prevents duplicate activation events. | Tech Lead | `TC-FR-066-005` |

## 16. Sign-off Checklist
1. All inherited requirements are mapped in Section 14.
2. All mapped requirements have at least one acceptance test in Section 13.
3. Lifecycle transitions and activation precedence are internally consistent.
4. Rollback and in-flight stability behavior are explicitly deterministic.
5. Domain objects align with parent SRS conceptual data model.
6. Lifecycle APIs and audit events cover all DFR behaviors in Section 4.
7. API operation semantics cover idempotency, conflict handling, and deterministic retries.
8. No contradiction exists with adjacent SRS domains (`SRS-02`, `SRS-03`, `SRS-04`, `SRS-09`, `SRS-10`).

## 17. Open Issues
1. In-flight instance migration between versions is deferred and out of scope for current baseline.
2. Multi-timezone activation scheduling UX details (display, warnings, and conversions) remain for UX specification.
3. Operational policy for conflict alert routing (who receives activation-gap and tie incidents) remains for Ops runbook definition.
4. Multi-company ownership migration scenarios (company merge/split) remain for future governance specification.

## 18. Next Document
After approval of `SRS-01`, proceed to `srs_04_runtime_orchestration_conditions.md`.
