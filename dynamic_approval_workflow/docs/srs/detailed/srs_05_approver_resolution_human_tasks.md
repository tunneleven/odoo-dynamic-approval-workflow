# SRS-05 Approver Resolution and Human Tasks

Version: `v1.2-draft`
Date: `2026-03-01`
Parent: `dynamic_approval_workflow_srs_v1.3.md`
Master Traceability: `srs_00_master_traceability.md`

## 1. Purpose
Define detailed requirements for approver resolution logic, human approval task lifecycle, delegation and control policies, follower behavior, and mobile usability for core approver actions.

## 2. Scope
In scope:
1. Approver source resolution across users, groups, hierarchy, and field references.
2. Delegation, anti-self-approval, and separation-of-duty controls.
3. Task lifecycle, user actions, SLA deadlines, reminders, and escalation.
4. Batch approve/reject with per-record permission checks and partial-success reporting.
5. Follower auto-subscription and completion policies.
6. Mobile compatibility for core approver actions.

Out of scope:
1. Workflow diagram modeling and viewer (`SRS-03`).
2. Runtime token execution engine internals (`SRS-04`).
3. Signature evidence policy semantics (`SRS-06`).

## 3. Inherited Requirement Coverage
- FR: `FR-029..042`, `FR-047..050`, `FR-074`
- NFR: `NFR-014`

## 4. Decomposed Detailed Requirements (DFR)
| DFR ID | Statement | Maps To |
|---|---|---|
| `DFR-05-001` | Approver resolution shall support named users as direct approvers. | `FR-029` |
| `DFR-05-002` | Approver resolution shall support groups/roles with deterministic member expansion: direct members first, then inherited group members in group-hierarchy depth order, de-duplicated by user ID with earliest-encountered entry retained. | `FR-030` |
| `DFR-05-003` | Approver resolution shall support requester hierarchy rules (manager chain). | `FR-031` |
| `DFR-05-004` | Approver resolution shall support record field references to dynamic approvers. | `FR-032` |
| `DFR-05-005` | Delegation shall support validity window and delegated actor traceability. | `FR-033` |
| `DFR-05-006` | Anti-self-approval shall block self-approval when configured. | `FR-034` |
| `DFR-05-007` | Separation-of-duty constraints shall prevent prohibited role/user combinations when configured. | `FR-035` |
| `DFR-05-008` | Step policy shall support minimum approver counts and quorum thresholds. | `FR-036` |
| `DFR-05-009` | Active approvers shall generate approval tasks with deterministic assignment metadata. | `FR-037` |
| `DFR-05-010` | Task actions shall include approve/reject/request_changes/delegate. | `FR-038` |
| `DFR-05-011` | Tasks shall support SLA deadline semantics with due timestamp behavior. | `FR-039` |
| `DFR-05-012` | Timed escalation rules shall be supported per task and step. | `FR-040` |
| `DFR-05-013` | Reminder schedules shall be configurable for pending tasks. | `FR-041` |
| `DFR-05-014` | Full task transition history shall be immutable and queryable. | `FR-042` |
| `DFR-05-015` | Follower policies shall support creator/requester auto-follow, active approver auto-follow, event-based extra followers, and completion downgrade/removal rules. | `FR-047`, `FR-048`, `FR-049`, `FR-050` |
| `DFR-05-016` | Batch approve/reject shall enforce per-record permission checks and report partial success deterministically. | `FR-074` |
| `DFR-05-017` | Core approver actions shall be mobile-compatible for supported form factors. | `NFR-014` |

## 5. Domain Objects (Conceptual)
1. `workflow.approver_resolution_rule`
- Source type, fallback policy, and conflict rules.
2. `workflow.approval_task`
- Human task record with assignment and SLA metadata.
3. `workflow.task_transition`
- Immutable transition event stream.
4. `workflow.delegation_rule`
- Delegator, delegate, validity window, and policy flags.
5. `workflow.follower_subscription`
- Auto-follow and event-follow policy state.

## 6. Approver Resolution Contract
### 6.1 Source Types
1. `named_user`
2. `group_role`
3. `requester_hierarchy`
4. `record_field_ref`

### 6.2 Resolution Order and De-duplication
1. Resolution order is configured per step; output is deterministic sorted actor list.
2. Duplicate actors from multiple sources are collapsed to one approver identity.
3. Disabled users, inactive employees, or access-invalid users shall be excluded from the resolved set with a structured warning event (`workflow.approver.excluded`) containing `user_id`, `exclusion_reason`, and `step_id`. If the resulting set is empty after exclusion, the step shall enter incident state per §6.3.

### 6.3 Fallback Behavior
1. If resolved set is empty and fallback is configured, the fallback source shall be executed. Valid fallback source types are:
   - `fallback_group`: a secondary group/role to expand
   - `fallback_hierarchy_level`: skip to next manager level in requester hierarchy
   - `fallback_named_users`: explicit fallback user list
   - `fallback_escalation_target`: use step escalation target as approver
2. Fallback sources are evaluated in configured priority order; first non-empty result wins.
3. If all fallback sources still produce an empty set, step enters incident state with `reason_code = no_approver_resolved`.

### 6.4 Policy Constraints
1. Anti-self and SoD constraints run after source expansion and before task creation.
2. Violations block task activation and produce structured policy error.

## 7. Delegation, Anti-Self, and SoD
### 7.1 Delegation Rules
1. Delegation requires validity period (`valid_from_utc`, `valid_to_utc`).
2. Delegation cannot outlive delegator account validity.
3. Delegated actions retain original task owner and acting delegate in audit.

### 7.2 Anti-Self Policy
1. If requester is also resolved approver and anti-self policy is enabled, requester must be removed or blocked per policy.
2. Removed requester is logged in policy evidence.

### 7.3 Separation-of-Duty
1. SoD policies define prohibited combinations (actor, role, prior action).
2. Violating actor is blocked from action and explicit SoD reason is shown.

## 8. Human Task Lifecycle Contract
### 8.1 Task States
1. `pending`
2. `in_progress`
3. `approved`
4. `rejected`
5. `changes_requested`
6. `delegated`
7. `escalated`
8. `cancelled`

### 8.2 Actions
1. `approve`
2. `reject`
3. `request_changes`
4. `delegate`

### 8.3 SLA, Reminder, Escalation
1. SLA due time is calculated at task creation.
2. Reminder schedules are relative to due time and the **policy calendar**.
   - Policy calendar defines working hours, working days, and holidays per company/group scope.
   - If no policy calendar is configured, reminders and SLA calculations use 24/7 UTC as default.
   - Business-hours SLA mode is deferred to future enhancement; v1 uses elapsed-time mode only.
3. Escalation executes on deadline breach according to step policy.
4. Escalation targets are resolved through same identity validation rules.

### 8.4 History and Audit
1. Every state transition is immutable.
2. Transition includes actor, action, timestamp, reason code, and correlation IDs.

## 9. Batch Action Contract (`FR-074`)
1. Batch operation accepts task list and intended action.
2. Permission and policy checks are evaluated per record/task.
3. Batch result returns:
- total requested
- succeeded count
- failed count
- per-record result details
4. Partial success is allowed and required to be explicitly reported.

## 10. Follower Policy Contract
### 10.1 Auto-follow Rules
1. Creator/requester auto-follow configurable.
2. Active approver auto-follow configurable.
3. Extra follower rules configurable by step/event.

### 10.2 Completion Policy
1. At completion, followers can be retained, downgraded, or removed by policy.
   - **Retained**: follower subscription unchanged; continues receiving all configured notification types.
   - **Downgraded**: follower subscription is narrowed to read-only notifications only (outcome summary); assignment/reminder/escalation notifications are suppressed.
   - **Removed**: follower subscription is deleted; no further notifications.
2. Default completion policy when unconfigured: **retained**.
3. Policy action on followers is auditable.

## 11. Mobile Compatibility Contract (`NFR-014`)
1. Core actions (`approve`, `reject`, `request_changes`, `delegate`) must be available on supported mobile viewports.
2. Task list and task detail shall remain usable with responsive layout.
3. Supported mobile baseline profile:
   - 390×844 viewport (minimum)
   - touch-only interaction
   - no horizontal scroll for core action controls
4. Additional viewport profiles may be added based on analytics data; the 390×844 baseline is the mandatory minimum.
1. `resolve_approvers(instance_id, step_id)`
2. `create_tasks(instance_id, step_id, approver_set)`
3. `perform_task_action(task_id, action, actor, payload)`
4. `delegate_task(task_id, delegate_actor, actor, reason_code)`
5. `run_task_sla_evaluation(task_id)`
6. `run_reminder_schedule(task_id)`
7. `run_escalation(task_id)`
8. `batch_task_action(task_ids, action, actor, payload)`
9. `apply_follower_policy(instance_id, event_type)`

### 12.2 Required Audit Events
1. `workflow.approver.resolved`
2. `workflow.approver.policy_blocked`
3. `workflow.task.created`
4. `workflow.task.transitioned`
5. `workflow.task.delegated`
6. `workflow.task.reminder_sent`
7. `workflow.task.escalated`
8. `workflow.task.batch_action_completed`
9. `workflow.follower.updated`

## 13. Acceptance Criteria and Test Scenarios
| Test ID | Requirement IDs | Scenario | Expected Result |
|---|---|---|---|
| `TC-FR-029-001` | `FR-029` | Resolve named-user approver set | Correct user set resolved |
| `TC-FR-030-001` | `FR-030` | Resolve group/role approvers | Group members resolved deterministically |
| `TC-FR-031-001` | `FR-031` | Resolve requester manager chain | Hierarchy approver resolved per policy |
| `TC-FR-032-001` | `FR-032` | Resolve approver from record field | Field-based actor resolved correctly |
| `TC-FR-033-001` | `FR-033` | Delegate within valid period | Delegation accepted and audited |
| `TC-FR-033-002` | `FR-033` | Delegate outside validity period | Delegation rejected |
| `TC-FR-034-001` | `FR-034` | Requester appears in approver set with anti-self enabled | Self-approval prevented |
| `TC-FR-035-001` | `FR-035` | SoD prohibited actor attempts approval | Action blocked with SoD reason |
| `TC-FR-036-001` | `FR-036` | Step with min approver and quorum policy | Completion follows quorum/min policy |
| `TC-FR-037-001` | `FR-037` | Activate step with resolved approvers | Tasks created for active approvers |
| `TC-FR-038-001` | `FR-038` | Execute approve/reject/request_changes/delegate actions | Actions transition tasks correctly |
| `TC-FR-039-001` | `FR-039` | Task reaches SLA deadline | SLA status reflects overdue state |
| `TC-FR-040-001` | `FR-040` | Overdue task escalation policy | Escalation executed and audited |
| `TC-FR-041-001` | `FR-041` | Pending task reminder schedule | Reminder dispatched as configured |
| `TC-FR-042-001` | `FR-042` | Query task history after multiple transitions | Complete immutable history returned |
| `TC-FR-047-001` | `FR-047` | Creator/requester auto-follow enabled | Requester subscribed as follower |
| `TC-FR-048-001` | `FR-048` | Active approver auto-follow enabled | Approver follower subscription created |
| `TC-FR-049-001` | `FR-049` | Event-based extra follower rule | Extra follower added on configured event |
| `TC-FR-050-001` | `FR-050` | Completion downgrade/removal policy | Followers adjusted per policy |
| `TC-FR-074-001` | `FR-074` | Batch approve mixed authorized/unauthorized tasks | Partial success with per-record reporting |
| `TC-NFR-014-001` | `NFR-014` | Execute core approver actions on baseline mobile viewport | Core actions usable without layout break |
| `TC-FR-036-002` | `FR-036`, `FR-042` | Multiple approvers race to satisfy quorum | Deterministic resolution and full audit history |
| `TC-FR-030-002` | `FR-030` | Resolve group with inherited/nested membership | Expansion follows depth-order, de-duplicates correctly |
| `TC-FR-035-002` | `FR-035` | SoD constraint with delegation chain | Delegated actor also blocked by SoD rules |
| `TC-FR-033-003` | `FR-033` | Delegation validity exactly at boundary timestamp | Boundary is inclusive for start, exclusive for end |
| `TC-FR-074-002` | `FR-074` | Batch action with mix of signed/unsigned tasks | Per-task policy enforced; partial success reported |

## 14. Traceability Matrix
| Canonical ID | Covered Sections | Primary Tests |
|---|---|---|
| `FR-029` | 4, 6 | `TC-FR-029-001` |
| `FR-030` | 4, 6 | `TC-FR-030-001` |
| `FR-031` | 4, 6 | `TC-FR-031-001` |
| `FR-032` | 4, 6 | `TC-FR-032-001` |
| `FR-033` | 4, 7 | `TC-FR-033-001`, `TC-FR-033-002` |
| `FR-034` | 4, 7 | `TC-FR-034-001` |
| `FR-035` | 4, 7 | `TC-FR-035-001` |
| `FR-036` | 4, 6, 8 | `TC-FR-036-001`, `TC-FR-036-002` |
| `FR-037` | 4, 8 | `TC-FR-037-001` |
| `FR-038` | 4, 8 | `TC-FR-038-001` |
| `FR-039` | 4, 8 | `TC-FR-039-001` |
| `FR-040` | 4, 8 | `TC-FR-040-001` |
| `FR-041` | 4, 8 | `TC-FR-041-001` |
| `FR-042` | 4, 8 | `TC-FR-042-001`, `TC-FR-036-002` |
| `FR-047` | 4, 10 | `TC-FR-047-001` |
| `FR-048` | 4, 10 | `TC-FR-048-001` |
| `FR-049` | 4, 10 | `TC-FR-049-001` |
| `FR-050` | 4, 10 | `TC-FR-050-001` |
| `FR-074` | 4, 9 | `TC-FR-074-001` |
| `NFR-014` | 4, 11 | `TC-NFR-014-001` |

## 15. Edge Case Register
| Edge Case ID | Edge Case | Expected Behavior | Owner | Linked Test ID |
|---|---|---|---|---|
| `EC-05-01` | Approver resolved from multiple sources appears duplicated | Duplicate identities collapsed before task creation | Tech Lead | `TC-FR-030-002` |
| `EC-05-02` | All resolved approvers filtered by anti-self/SoD | Step blocked with policy incident `no_eligible_approver` | Workflow Admin | `TC-FR-035-002` |
| `EC-05-03` | Delegate becomes inactive during validity window | Task reverts to fallback assignee policy and incident logged | Workflow Admin | `TC-FR-033-003` |
| `EC-05-04` | Batch request includes already terminal tasks | Terminal tasks reported as skipped with reason; others processed | QA Lead | `TC-FR-074-002` |

## 16. Sign-off Checklist
1. All inherited requirements in Section 3 are mapped in Section 14.
2. Resolution order, anti-self, and SoD constraints are deterministic.
3. Batch partial-success contract includes per-record details.
4. Task history immutability aligns with audit/event policy.
5. Mobile baseline profile is explicit and testable.
6. Cross-links to `SRS-06` (signature actions) and `SRS-07` (access checks) are coherent.

## 17. Open Issues
1. Final UX behavior for multi-level hierarchy fallback (skip-level manager policy) requires product sign-off.
2. Calendar/timezone business-hour escalation profile requires operational configuration baseline.

## 18. Next Document
After approval of `SRS-05`, proceed to `srs_06_signature_evidence_policy.md`.
