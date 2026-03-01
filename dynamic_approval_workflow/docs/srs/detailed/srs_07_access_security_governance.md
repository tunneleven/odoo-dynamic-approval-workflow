# SRS-07 Access Provisioning, Security, and Governance

Version: `v1.2-draft`
Date: `2026-03-01`
Parent: `dynamic_approval_workflow_srs_v1.3.md`
Master Traceability: `srs_00_master_traceability.md`

## 1. Purpose
Define detailed requirements for RBAC, temporary access provisioning lifecycle, immutable audit governance, snippet sandbox controls, and strict multi-company isolation.

## 2. Scope
In scope:
1. Temporary access grant/revoke lifecycle for approvers.
2. Least-privilege and multi-company-scoped access controls.
3. RBAC permissions for designer/admin/approver/auditor roles.
4. Immutable audit timeline for config/runtime security events.
5. Snippet editing governance and sandbox runtime restrictions.
6. Configuration versioning for governance-sensitive changes.

Out of scope:
1. Human task assignment logic (`SRS-05`).
2. Signature evidence domain specifics (`SRS-06`).
3. Notification/webhook delivery semantics (`SRS-08`).

## 3. Inherited Requirement Coverage
- FR: `FR-051..055`, `FR-061..065`, `FR-079`
- NFR: `NFR-007`, `NFR-010`, `NFR-012`

## 4. Decomposed Detailed Requirements (DFR)
| DFR ID | Statement | Maps To |
|---|---|---|
| `DFR-07-001` | Temporary access grants shall be created automatically for approvers when access is required for pending task execution. | `FR-051` |
| `DFR-07-002` | Temporary grants shall be least-privilege and rule-scoped to specific operations/records. | `FR-052` |
| `DFR-07-003` | Temporary grants shall be revoked/downgraded deterministically when no longer required. | `FR-053` |
| `DFR-07-004` | All access grants/revocations shall be immutable and queryable in security audit logs. | `FR-054`, `NFR-010` |
| `DFR-07-005` | Access provisioning shall enforce multi-company boundaries for grant creation, usage, and revocation. | `FR-055`, `FR-079`, `NFR-007` |
| `DFR-07-006` | RBAC shall enforce role permissions for designer/admin/approver/auditor actions. | `FR-061` |
| `DFR-07-007` | System shall preserve immutable audit timeline for configuration and runtime security-sensitive actions. | `FR-062` |
| `DFR-07-008` | Advanced snippet editing shall be restricted to admin-only policy scope. | `FR-063` |
| `DFR-07-009` | Snippet execution shall run in sandbox with runtime limits and forbidden operations enforcement. | `FR-064`, `NFR-012` |
| `DFR-07-010` | Configuration changes shall be versioned with actor and timestamp. | `FR-065` |

## 5. Domain Objects (Conceptual)
1. `workflow.access_grant`
- Temporary privilege grant with scope, issuer, and expiry.
2. `workflow.access_grant_log`
- Immutable grant/revoke lifecycle event records.
3. `workflow.security_policy`
- RBAC, sandbox, and governance policy versions.
4. `workflow.snippet_execution_event`
- Sandbox execution outcome and violation metadata.
5. `workflow.config_version_event`
- Versioned config change event for governance.

## 6. RBAC and Permission Contract
### 6.1 Roles
1. `workflow_designer`
2. `workflow_admin`
3. `workflow_approver`
4. `workflow_auditor`

### 6.2 Permission Boundaries
1. Designer can author definitions but cannot override security policies.
2. Admin can manage bindings, security policies, and emergency recovery controls.
3. Approver can act on authorized tasks and view scoped runtime artifacts.
4. Auditor has read-only access to audit artifacts.

### 6.3 Deny-by-Default
1. Any action outside role policy is denied with reason code.
2. Permission checks execute server-side and are non-bypassable from client.

## 7. Temporary Access Provisioning Contract
### 7.1 Grant Mechanics
1. Grant types include group membership grant and record-scope rule grant.
2. Grant selection is policy-driven; `sudo` is not a grant mechanism.
3. Grant scope includes:
- target model
- target operation set
- company scope
- optional record domain constraints
4. Grant TTL shall be explicit and bounded:
   - Minimum TTL: 5 minutes (prevents grant churn from rapid task cycling).
   - Maximum TTL: 72 hours (prevents indefinite privilege accumulation).
   - Default TTL: 24 hours (used when step policy does not specify).
   - Grants exceeding maximum TTL shall be rejected at creation.

### 7.2 Grant Activation and Cache Behavior
1. Grant activation must be effective before task action becomes executable.
2. Security cache invalidation is required on grant create/revoke operations.
3. Cache invalidation failures raise security incidents and block unsafe continuation.

### 7.3 Revoke Guarantees
1. Revocation triggers on task completion/cancellation/timeout or policy event.
2. Revoke must be idempotent and verifiable.
3. System must reconcile orphan grants via scheduled consistency job.

### 7.4 `sudo` and Elevated Context Boundaries
1. `sudo` may be used only in explicit allow-listed system flows.
2. `sudo` usage must emit elevated-context audit events.
3. User-driven actions must not silently escalate to `sudo`.

## 8. Multi-Company Isolation Contract
1. Access grant creation requires actor company compatibility with target records.
2. Cross-company grants are disallowed unless explicit policy exists and is audited.
3. Query filters enforce company isolation in tasks, diagrams, and audit data.
4. Any cross-company mismatch creates security incident and denies action.

## 9. Snippet Governance and Sandbox Contract
### 9.1 Editing Governance
1. Advanced snippet editing is admin-only.
2. Snippet policy changes require config version event and approval workflow.

### 9.2 Sandbox Runtime Rules
1. Enforce runtime limits:
- execution timeout
- memory limit
- operation whitelist
2. Forbidden operations include network calls, filesystem access, and unsafe imports unless explicitly allow-listed.
3. Violations are blocked and logged as security events.

### 9.3 Deterministic Failure Semantics
1. Sandbox failure cannot produce partial privileged side effects.
2. On violation, action outcome is failed-safe and auditable.

## 10. Audit and Configuration Versioning Contract
1. Audit timeline is immutable and append-only.
2. Audit event includes actor, principal type, timestamp, object reference, and payload hash.
3. Config changes generate version event with before/after hashes.
4. Security-sensitive config rollbacks require explicit approval and reason.

## 11. APIs and Events (Security Domain)
### 11.1 Logical Operations
1. `evaluate_rbac(actor, action, object_ref)`
2. `provision_temporary_access(task_id, actor)`
3. `revoke_temporary_access(grant_id, actor)`
4. `reconcile_orphan_grants()`
5. `execute_snippet_sandboxed(snippet_id, context)`
6. `record_config_version_change(object_ref, actor, delta)`

### 11.2 Required Audit Events
1. `workflow.security.rbac_denied`
2. `workflow.security.access_grant_created`
3. `workflow.security.access_grant_revoked`
4. `workflow.security.access_grant_reconciled`
5. `workflow.security.elevated_context_used`
6. `workflow.security.sandbox_violation`
7. `workflow.security.config_versioned`
8. `workflow.security.cross_company_blocked`

## 12. Acceptance Criteria and Test Scenarios
| Test ID | Requirement IDs | Scenario | Expected Result |
|---|---|---|---|
| `TC-FR-051-001` | `FR-051` | Pending task requires extra access | Temporary access grant automatically created |
| `TC-FR-052-001` | `FR-052` | Grant generated for task | Scope limited to least privilege needed |
| `TC-FR-053-001` | `FR-053` | Task completed | Grant revoked/downgraded deterministically |
| `TC-FR-054-001` | `FR-054`, `NFR-010` | Grant and revoke lifecycle | Full immutable grant/revoke audit available |
| `TC-FR-055-001` | `FR-055`, `FR-079`, `NFR-007` | Attempt cross-company grant without policy | Operation denied and incident logged |
| `TC-FR-061-001` | `FR-061` | User attempts action outside RBAC role | Action denied with reason |
| `TC-FR-062-001` | `FR-062` | Query security timeline after runtime/config actions | Immutable timeline returned |
| `TC-FR-063-001` | `FR-063` | Non-admin tries advanced snippet edit | Operation denied |
| `TC-FR-064-001` | `FR-064`, `NFR-012` | Snippet performs forbidden operation | Sandbox blocks execution and logs violation |
| `TC-FR-065-001` | `FR-065` | Config update applied | Versioned change event stored with actor/timestamp |
| `TC-NFR-007-001` | `NFR-007` | Multi-company query isolation check | No cross-company data leakage |
| `TC-NFR-010-001` | `NFR-010` | Trace access grant lifecycle for specific incident | Full traceability achieved |
| `TC-NFR-012-001` | `NFR-012` | Sandbox limit exceeded | Operation stopped and violation recorded |
| `TC-FR-053-002` | `FR-053`, `FR-054` | Revoke attempt repeated (idempotent retry) | Single effective revoke and consistent audit trail |
| `TC-FR-051-002` | `FR-051`, `FR-054` | Cache invalidation fails after grant | Security incident raised and unsafe action blocked |
| `TC-FR-053-003` | `FR-053` | Grant revoke job delayed beyond TTL | Reconciliation job revokes stale grants; correction logged |
| `TC-FR-055-002` | `FR-055`, `NFR-007` | Approver changes company during active task | Incompatible grant revoked; task blocked |
| `TC-FR-054-002` | `FR-054` | Concurrent grant and revoke on same task | Deterministic final state; idempotent audit |

## 13. Traceability Matrix
| Canonical ID | Covered Sections | Primary Tests |
|---|---|---|
| `FR-051` | 4, 7 | `TC-FR-051-001`, `TC-FR-051-002` |
| `FR-052` | 4, 7 | `TC-FR-052-001` |
| `FR-053` | 4, 7 | `TC-FR-053-001`, `TC-FR-053-002` |
| `FR-054` | 4, 10 | `TC-FR-054-001`, `TC-FR-053-002`, `TC-FR-051-002` |
| `FR-055` | 4, 8 | `TC-FR-055-001` |
| `FR-061` | 4, 6 | `TC-FR-061-001` |
| `FR-062` | 4, 10 | `TC-FR-062-001` |
| `FR-063` | 4, 9 | `TC-FR-063-001` |
| `FR-064` | 4, 9 | `TC-FR-064-001` |
| `FR-065` | 4, 10 | `TC-FR-065-001` |
| `FR-079` | 4, 8 | `TC-FR-055-001`, `TC-NFR-007-001` |
| `NFR-007` | 4, 8 | `TC-NFR-007-001` |
| `NFR-010` | 4, 10 | `TC-NFR-010-001`, `TC-FR-054-001` |
| `NFR-012` | 4, 9 | `TC-NFR-012-001`, `TC-FR-064-001` |

## 14. Edge Case Register
| Edge Case ID | Edge Case | Expected Behavior | Owner | Linked Test ID |
|---|---|---|---|---|
| `EC-07-01` | Grant created but revoke job delayed | Reconciliation job revokes stale grants and logs correction | Security Lead | `TC-FR-053-003` |
| `EC-07-02` | Approver moves company during active task | Grant reevaluated; incompatible access revoked and task blocked | Workflow Admin | `TC-FR-055-002` |
| `EC-07-03` | Concurrent grant + revoke on same task | Deterministic final state with idempotent logs | Tech Lead | `TC-FR-054-002` |

## 15. Sign-off Checklist
1. All inherited requirements in Section 3 are mapped in Section 13.
2. Access grant/revoke mechanics are explicit and auditable.
3. Cache invalidation and revoke guarantees are defined.
4. `sudo` boundaries are explicit and non-silent.
5. Multi-company isolation controls align with global policy.
6. Sandbox governance and violation semantics are testable.

## 16. Open Issues
1. Exact cache invalidation implementation strategy depends on deployment topology and requires architecture decision record.
2. Cross-company exception policy governance requires security council approval.

## 17. Next Document
After approval of `SRS-07`, proceed to `srs_08_notifications_webhooks_external_contracts.md`.
