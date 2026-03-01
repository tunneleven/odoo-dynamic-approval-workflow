# Software Requirements Specification (SRS)

## Dynamic Approval Workflow Module for Odoo 19

## Version
- `v1.2`

## Date
- `2026-02-26`

## 1. Purpose
This document defines the requirements for a new configurable approval workflow module for Odoo 19. The module must support dynamic, UI-driven workflow configuration and runtime execution across eligible form actions without per-feature code customization.

This SRS is concept-driven using external workflow best-practice patterns (BPMN engines, durable orchestration, and human-task workflows), then adapted for Odoo implementation constraints.

## 2. Product Goals
1. Provide a single approval/workflow framework reusable across business apps.
2. Enable business administrators to configure flows from UI.
3. Support complex approval logic: multi-step, conditional branching, parallel paths, escalation.
4. Preserve native Odoo UI behavior through JS hook integration rather than destructive replacement.
5. Ensure enterprise governance: auditability, role security, access control automation, and optional digital signature.

## 3. Scope

## 3.1 In Scope
1. Workflow definition, versioning, publishing, and rollback.
2. Binding workflow to model/action/form runtime through configuration.
3. BPMN modeling and runtime visualization with `bpmn-js`.
4. Executable BPMN subset support.
5. Dynamic approver resolution and human task lifecycle.
6. Optional digital signature for approval actions.
7. Auto follower management on records.
8. Automatic temporary approver access grants and revocation.
9. Notifications through in-app, email, and webhooks.
10. Monitoring, incident handling, and audit reports.

## 3.2 Out of Scope
1. Full BPMN 2.0 execution parity in initial release.
2. Mandatory chat/SMS notification channels in initial release.
3. Hard lock-in to one external workflow engine.

## 4. Stakeholders and Actors
1. Workflow Designer: configures and publishes workflow definitions.
2. Workflow Admin: governs security, runtime settings, incidents, and policies.
3. Request Creator: creates business record and tracks approval progress.
4. Approver: reviews and executes approval tasks.
5. Auditor/Compliance Officer: reviews immutable approval and signature evidence.
6. System Integrator: consumes webhook events and integrates external services.

## 5. Assumptions and Constraints
1. Target profile is medium enterprise: multi-company, moderate concurrency, about 1k approvals/day baseline.
2. Workflow execution is pluggable by architecture; internal runtime is allowed initially.
3. `bpmn-js` is mandatory for diagram design/view.
4. Advanced Python snippets are optional and restricted to admin-only with sandbox and audit.
5. Eligible integration scope is any model with compatible form/action behavior.

## 6. High-Level Functional Overview
1. Admin defines workflow in UI and links it to a target model/action.
2. Triggered record enters workflow instance.
3. Engine resolves active step(s), approvers, and conditions.
4. Approvers receive tasks and notifications.
5. Approvers act (approve/reject/request changes/delegate/escalate).
6. Engine advances based on conditions/joins.
7. Final state unblocks or blocks business action.
8. Full timeline, diagram state, signature evidence, and audit logs remain available.

## 7. Functional Requirements

## 7.1 Workflow Definition and Versioning
1. `FR-001`: The system shall allow workflow creation from UI without code changes.
2. `FR-002`: The system shall support `draft`, `published`, and `archived` definition states.
3. `FR-003`: Published versions shall be immutable.
4. `FR-004`: The system shall support cloning a published version to a new draft.
5. `FR-005`: The system shall validate structure and logic before publish.
6. `FR-006`: The system shall support effective-date version activation.

## 7.2 Binding and Runtime Integration
1. `FR-007`: The system shall bind workflow to model/action by configuration.
2. `FR-008`: The system shall gate target action execution until required approvals complete.
3. `FR-009`: The system shall integrate workflow UI in form view using JS hooks.
4. `FR-010`: JS integration shall not replace existing native form elements by default.
5. `FR-011`: The system shall allow per-binding rollout by company/group/domain.
6. `FR-012`: The system shall allow enable/disable of binding without deleting definition.
7. `FR-071`: The system shall allow the request creator to withdraw/cancel a pending approval instance based on configured policy.
8. `FR-072`: The system shall allow Workflow Admin forced reassignment of pending tasks.
9. `FR-081`: The system shall expose explicit gating state to the frontend hook for each bound action (`blocked`, `allowed`, `allowed_with_warning`).

## 7.3 BPMN Modeling and Diagram UX
1. `FR-013`: The system shall use `bpmn-js` for workflow modeler UI.
2. `FR-014`: The system shall provide drag-and-drop BPMN workflow authoring using `bpmn-js`.
3. `FR-015`: The system shall convert BPMN drag-and-drop diagram elements into executable metadata, where `bpmn_xml` is canonical and compiled metadata is a versioned derived artifact.
4. `FR-016`: The system shall use `bpmn-js` for runtime diagram viewer.
5. `FR-017`: The system shall import/export BPMN XML for supported subset.
6. `FR-018`: The system shall show validation errors for unsupported BPMN elements.
7. `FR-019`: Creator and approver roles shall have runtime diagram visibility.
8. `FR-020`: Runtime diagram shall highlight current node, completed nodes, and pending approvers.

## 7.4 Routing, Conditions, and Execution
1. `FR-021`: The system shall support sequential steps.
2. `FR-022`: The system shall support parallel branches.
3. `FR-023`: The system shall support conditional branching based on record data/context.
4. `FR-024`: The system shall support join behavior: `all`, `any`, and `quorum`.
5. `FR-025`: The system shall support rework/request-change loop paths.
6. `FR-026`: The system shall support no-code condition builder.
7. `FR-027`: The system shall support optional admin-only advanced Python snippets with sandbox controls.
8. `FR-028`: The system shall provide simulation/dry-run validation prior to publishing.
9. `FR-073`: The system shall support timeout auto-decision policies per step (`auto-approve`, `auto-reject`, `escalate-only`).
10. `FR-082`: Quorum shall be configurable per step as either absolute count or percentage, with optional minimum absolute floor.

## 7.5 Dynamic Approver Resolution
1. `FR-029`: The system shall resolve approvers from named users.
2. `FR-030`: The system shall resolve approvers from groups/roles.
3. `FR-031`: The system shall resolve approvers from requester hierarchy (manager rules).
4. `FR-032`: The system shall resolve approvers from record field references.
5. `FR-033`: The system shall support delegation with validity period.
6. `FR-034`: The system shall enforce anti-self-approval when configured.
7. `FR-035`: The system shall enforce separation-of-duty constraints when configured.
8. `FR-036`: The system shall support minimum approver and quorum policies per step.

## 7.6 Human Task Lifecycle
1. `FR-037`: The system shall create approval tasks for active approvers.
2. `FR-038`: The system shall support approve, reject, request changes, and delegate actions.
3. `FR-039`: The system shall support SLA deadline on tasks.
4. `FR-040`: The system shall support timed escalation rules.
5. `FR-041`: The system shall support reminder scheduling for pending tasks.
6. `FR-042`: The system shall keep complete task transition history.
7. `FR-074`: The system shall support batch approval/rejection actions across multiple tasks with per-record permission checks and partial-success reporting.

## 7.7 Digital Signature
1. `FR-043`: The system shall support optional digital-sign-required policy per step.
2. `FR-044`: The system shall require signature evidence before marking signed approval complete.
3. `FR-045`: The system shall store immutable signature evidence fields: signer, timestamp, method, and reference/hash.
4. `FR-046`: The system shall separate standard approval and signed approval in audit logs.

## 7.8 Record Followers
1. `FR-047`: The system shall support auto-follow rules for creator/requester.
2. `FR-048`: The system shall support auto-follow rules for active approvers.
3. `FR-049`: The system shall support configurable extra follower rules by step/event.
4. `FR-050`: The system shall support optional follower removal/downgrade policy at completion.

## 7.9 Automatic Access Provisioning
1. `FR-051`: The system shall grant required temporary access to approvers automatically.
2. `FR-052`: The access scope shall be least-privilege and rule-based.
3. `FR-053`: The system shall revoke/downgrade temporary access once no longer needed.
4. `FR-054`: Access grants and revocations shall be fully auditable.
5. `FR-055`: Access provisioning shall support multi-company constraints.

## 7.10 Notifications and External Integration
1. `FR-056`: The system shall send in-app notifications for assignment/reminders/escalation/outcome.
2. `FR-057`: The system shall send configurable email templates for key events.
3. `FR-058`: The system shall emit signed webhook events for lifecycle transitions.
4. `FR-059`: The system shall support retry and dead-letter handling for failed outbound events.
5. `FR-060`: Webhook events shall be idempotency-safe for consumers.
6. `FR-083`: Webhook signatures shall use HMAC-SHA256 with per-endpoint secret, timestamp header, and replay-window validation contract.

## 7.11 Security, Audit, and Governance
1. `FR-061`: The system shall enforce RBAC for designer/admin/approver/auditor permissions.
2. `FR-062`: The system shall keep immutable audit timeline for configuration and runtime actions.
3. `FR-063`: Admin-only advanced snippet editing shall be enforced by policy.
4. `FR-064`: Snippet execution shall be sandboxed with runtime limits and forbidden operations.
5. `FR-065`: All configuration changes shall be versioned with actor and timestamp.
6. `FR-066`: The system shall support rollback to prior published definition versions.

## 7.12 Operations and Monitoring
1. `FR-067`: The system shall provide dashboards for active, overdue, failed, and completed workflows.
2. `FR-068`: The system shall provide incident queue and safe retry/recovery actions.
3. `FR-069`: The system shall provide per-record trace including diagram state and event timeline.
4. `FR-070`: The system shall expose structured runtime metrics/logs for observability.

## 7.13 Additional Platform and Governance Requirements
1. `FR-075`: The system shall detect concurrent draft edits and enforce conflict policy (optimistic locking with merge/retry flow).
2. `FR-076`: The system shall support configurable archival and purge operations for completed workflow runtime data and logs according to retention policy.
3. `FR-077`: The system shall provide responsive/mobile-compatible approval task interaction for core actions.
4. `FR-078`: The system shall support localization for workflow labels, step descriptions, and notification templates.
5. `FR-079`: The system shall enforce multi-company isolation in all workflow queries, task assignment, and diagram visibility.

## 8. External Interfaces and Contracts

## 8.1 Logical API Contracts
1. Definition:
`workflow_definition { id, key, version, status, bpmn_xml, compiled_metadata, bindings, policies, publish_meta }`
2. Instance:
`workflow_instance { id, definition_key, definition_version, model, res_id, state, current_nodes, started_at, ended_at }`
3. Task:
`approval_task { id, instance_id, node_id, assignees, status, sla_due_at, escalated, sign_required }`
4. Audit:
`workflow_audit_event { id, event_type, actor, occurred_at, object_ref, payload_hash }`
5. Webhook:
`workflow_webhook_event { event_id, type, occurred_at, instance_ref, task_ref, payload, signature }`
6. Gate:
`workflow_gate_state { model, res_id, action_key, state, reason_code, instance_id }`

## 8.2 Runtime Adapter Contract (Pluggable Engine)
1. `deploy(definition)`
2. `validate(definition)`
3. `start(binding_context)`
4. `signal(instance_id, signal_type, payload)`
5. `complete_task(task_id, decision, payload)`
6. `get_instance_state(instance_id)`
7. `get_gate_state(binding_context)`
8. `cancel_instance(instance_id, reason)`
9. `reassign_task(task_id, assignee_ref, reason)`

## 8.3 Canonical Definition and Compilation Rules
1. `bpmn_xml` is the canonical source of truth for workflow process structure.
2. `compiled_metadata` is a deterministic, versioned derivative generated at publish time for runtime optimization.
3. Runtime execution shall consume `compiled_metadata` that is cryptographically tied to the canonical `bpmn_xml` hash.
4. Any change to `bpmn_xml` requires new definition version and recompilation.

## 8.4 Webhook Signing Profile
1. Signing algorithm: `HMAC-SHA256`.
2. Required headers: event id, timestamp, signature version, signature digest.
3. Key management: per-endpoint secret with rotation support and overlap window.
4. Verification contract: consumer validates signature and timestamp within replay window; duplicate `event_id` must be ignored idempotently.
5. Security posture: invalid signature or expired timestamp results in consumer-side rejection and producer retry policy handling.

## 9. Data Model (Conceptual)
1. `workflow.definition`
2. `workflow.definition.version`
3. `workflow.definition.compiled`
4. `workflow.definition.edit.session`
5. `workflow.binding`
6. `workflow.instance`
7. `workflow.node.runtime`
8. `workflow.task`
9. `workflow.approver.resolution`
10. `workflow.delegation.record`
11. `workflow.condition.rule`
12. `workflow.notification.template`
13. `workflow.signature.evidence`
14. `workflow.access.grant.log`
15. `workflow.follower.rule`
16. `workflow.audit.event`
17. `workflow.outbound.event`
18. `workflow.incident`
19. `workflow.retention.policy`
20. `workflow.archive.job`

## 10. Non-Functional Requirements
1. `NFR-001`: Availability target (99.9%) applies to workflow module runtime components (engine, task services, webhook dispatcher), excluding full host-instance outages outside module control.
2. `NFR-002`: P95 transition latency shall be below 2 seconds measured from accepted task decision API call to durable state transition commit and notification enqueue.
3. `NFR-003`: Runtime shall support baseline 1k approvals/day, burst factor 5x within 15 minutes, and at least 500 concurrent active instances.
4. `NFR-004`: State transitions on a single record shall be strongly consistent.
5. `NFR-005`: All external event deliveries shall be idempotency-safe.
6. `NFR-006`: Audit and signature evidence retention shall be policy-configurable.
7. `NFR-007`: Multi-company data isolation shall be strictly enforced.
8. `NFR-008`: In-flight instances shall remain stable across definition version changes.
9. `NFR-009`: Diagram viewer P95 load shall be under 1.5 seconds for standard-size flows.
10. `NFR-010`: Access grant lifecycle must be fully traceable and queryable.
11. `NFR-011`: JS hook integration shall not regress existing form interactions in supported modules.
12. `NFR-012`: Sandbox policy must block unsafe snippet operations and record violations.
13. `NFR-013`: Backup and restore shall support workflow state with maximum RPO 15 minutes and RTO 60 minutes.
14. `NFR-014`: Core approver actions shall be usable on mobile form factors.
15. `NFR-015`: Workflow configuration and runtime artifacts shall support i18n and timezone-aware rendering.

## 11. BPMN Subset Requirement Baseline
Supported in scope:
1. Start and End events.
2. User Task.
3. Exclusive gateway.
4. Parallel gateway.
5. Intermediate timer event.
6. Intermediate message/signal event (runtime-triggered semantics).
7. Sequence flows with condition expressions.

Excluded from first release:
1. Full event subprocess parity.
2. Complex gateway variants outside documented subset.
3. Choreography and collaboration execution semantics beyond viewer needs.

## 12. Validation and Test Scenarios
1. Publish validation rejects malformed BPMN XML.
2. Action gating blocks action until required approvals complete.
3. Parallel branch join with quorum executes correctly.
4. Conditional routing selects expected path for defined domain sets.
5. Delegation expires and reverts correctly.
6. SLA deadline triggers escalation and notifications.
7. Signed-approval step blocks completion without signature evidence.
8. Auto-follower rules add/remove expected users on transitions.
9. Temporary access grants allow approval action and are revoked on completion.
10. JS hook integration preserves native form actions and statusbar behavior.
11. Creator and approver can open diagram and see live step highlighting.
12. Webhook retry and dead-letter flow handle network failure safely.
13. Audit report reconstructs exact approval path and actors.
14. Creator withdraw/cancel path behaves according to policy and audit requirements.
15. Admin forced reassignment updates task ownership and notifications.
16. Timeout auto-decision executes configured behavior and captures reason code.
17. Batch approvals process with partial success and per-item error reporting.
18. Multi-company isolation prevents cross-company visibility and approval actions.
19. In-flight instances remain on previous definition after new version activation.
20. Sandbox violation attempts are blocked, logged, and do not affect runtime integrity.
21. Concurrent approvals on same quorum step are race-safe and deterministic.
22. Concurrent draft editing triggers optimistic lock conflict workflow.

## 13. Phased Delivery Plan and Acceptance Criteria

## Phase 0: SRS and Governance Baseline
1. Scope, roles, security, and compliance baseline approved.
2. Functional and NFR identifiers signed off.
3. BPMN subset boundary approved.

## Phase 1: Core Domain and Contracts
1. Canonical domain model approved.
2. Runtime adapter contract approved.
3. Versioning and lifecycle semantics approved.

## Phase 2: Config UX and Form Hook Integration
1. UI can define, validate, and publish workflows.
2. BPMN drag-and-drop authoring with `bpmn-js` is functional (design-time modeler only).
3. Diagram-to-definition compilation produces executable metadata for supported elements.
4. Binding UI supports model/action linkage with rollout scope.
5. Form integration works through JS hooks without replacing native elements.

## Phase 3: Runtime Orchestration and Access Automation
1. Sequential, parallel, and conditional execution works end-to-end.
2. Action gating and unblocking behavior validated.
3. Automatic approver access grants/revocations validated and audited.

## Phase 4: Human Tasks, Followers, and Notifications
1. Delegation, reminders, escalations, SLA states operational.
2. Auto-follower rules work on configured events.
3. In-app, email, and webhook delivery with retry/idempotency validated.
4. Batch approval/rejection behavior validated for permission-safe partial processing.

## Phase 5: BPMN UX and Diagram Runtime Visibility
1. `bpmn-js` runtime viewer integrated with live node/task overlays.
2. Import/export for supported BPMN subset validated.
3. Creator/approver runtime diagram visibility and highlighting validated.
4. Mobile runtime view fallback and localization rendering validated.

## Phase 6: Signature, Audit, and Production Readiness
1. Signed approval policy and immutable evidence validated.
2. Full audit traceability validated by compliance scenarios.
3. Performance, failover, and operational readiness targets met.

## 14. Risks and Mitigations
1. Risk: Overly broad BPMN scope.
Mitigation: Enforce documented executable subset with strict validator.
2. Risk: Permission leakage from auto access grants.
Mitigation: Least-privilege templates, short-lived grants, full revoke auditing.
3. Risk: UI regressions from form hook extension.
Mitigation: Compatibility contract and regression suite against representative models.
4. Risk: Unsafe advanced snippets.
Mitigation: Admin-only control, sandbox constraints, review workflow, audit logs.

## 15. Traceability Notes
1. All implementation user stories must reference one or more `FR-*`.
2. All test cases must trace to `FR-*` and `NFR-*`.
3. Release readiness requires coverage report by requirement ID.

## 16. Sandbox Specification Annex (Advanced Python Snippets)
1. Execution mode: snippets run asynchronously in worker context; UI request path must not directly execute arbitrary snippet code.
2. Forbidden operations: file I/O, network access, process spawning, dynamic imports, reflection/introspection of private runtime internals, and direct SQL execution.
3. Allowed data scope: read-only runtime context object, whitelisted helper functions, and deterministic utility libraries.
4. Resource limits per snippet execution: max wall-time 200 ms, max CPU-time 100 ms, max memory 16 MB.
5. Failure behavior: timeout or policy violation marks evaluation as failed-safe (`False`) and emits security audit event.
6. Governance: snippet create/update requires admin role and publish approval workflow; all changes are versioned and diff-audited.
