# Dynamic Approval Workflow Module for Odoo 19  
## SRS + Multi-Phase Delivery Plan (Concept-First, Non-Odoo Workflow References)

## 1. Summary
This SRS defines a new, standalone dynamic approval-workflow platform for Odoo 19 that is:
1. UI-configurable (no per-feature code changes for flow setup).
2. Applicable to any eligible form action/model.
3. Multi-step with conditional branching and parallel paths.
4. Notification-driven (in-app, email, webhook).
5. BPMN-integrated using an executable BPMN subset.
6. Governed for enterprise safety (auditability, RBAC, sandboxed advanced logic).
7. Engine-pluggable to avoid lock-in.

Implementation details are intentionally deferred; this is requirement-complete and phase-ready.

## 2. Brainstorm From Famous External Workflow Concepts
Reference concept families (outside Odoo) and extracted requirement signals:

| Reference family | Core concept | Requirement signal adopted |
|---|---|---|
| BPMN engines (Camunda, Flowable) | BPMN patterns, user tasks, timers/messages, incidents | Require executable BPMN subset, SLA timers, escalation, incident handling |
| Durable orchestration (Temporal) | Durable state/history, retries, determinism discipline | Require replay-safe execution semantics, idempotency, versioned definitions |
| JSON workflow engines (Conductor) | Dynamic fork/join, human task pause/resume | Require dynamic parallel approvals, explicit wait states, external completion hooks |
| Vendor-neutral DSL (CNCF Serverless Workflow) | Interoperable workflow definitions | Require import/export neutrality and pluggable runtime contract |
| Standards (OMG BPMN/DMN) | Shared notation + decision modeling | Require BPMN for flow and decision-table compatibility for complex rules |

Inference from sources: a practical enterprise scope should combine BPMN-first orchestration, decision-table-friendly routing, durable execution semantics, and strong human-task operations (delegation/escalation/SLA) rather than only simple step approval.

## 3. Product Scope
## 3.1 In Scope
1. Configurable workflow definition and versioning.
2. Binding workflow to eligible model actions/forms via configuration.
3. Runtime approval execution with branching, parallelism, and conditions.
4. Dynamic approver resolution (users/groups/roles/hierarchy/field-based/delegates/quorum).
5. Human task lifecycle controls (approve/reject/request-change/delegate/escalate/timeout).
6. Notification framework (in-app, email, webhook).
7. BPMN diagram modeling, import/export, and executable subset validation.
8. Full audit trail and operational observability.
9. Pluggable runtime interface for future external engine support.

## 3.2 Out of Scope (for current SRS baseline)
1. Full BPMN 2.0 execution parity.
2. Chat/SMS native notification channels.
3. Hard dependency on any single external engine.

## 4. Decision Baseline (Locked)
1. BPMN scope: executable BPMN subset.
2. MVP reach: any eligible model with form action support.
3. Scale target: medium enterprise, multi-company, ~1k approvals/day.
4. Rule style: no-code DSL/domain builder plus admin-only advanced Python snippets.
5. Approver model: complex hybrid dynamic model.
6. Notification channels: in-app + email + webhooks.
7. Human-task controls: delegation + escalation + SLA timers mandatory.
8. Engine strategy: pluggable runtime architecture.

## 5. Software Requirements Specification (SRS)
## 5.1 Functional Requirements

### A. Workflow Definition & Lifecycle
1. `FR-001`: System shall allow creation of workflow definitions from UI.
2. `FR-002`: System shall support draft, published, archived definition states.
3. `FR-003`: System shall support immutable published versions.
4. `FR-004`: System shall allow cloning published versions into new drafts.
5. `FR-005`: System shall support effective-date activation for versions.
6. `FR-006`: System shall validate definitions before publish (structural + semantic checks).

### B. Binding & Dynamic Integration
7. `FR-007`: System shall bind workflow definitions to model + trigger action without per-model code change.
8. `FR-008`: System shall support replacement/guarding of target action execution until approvals pass.
9. `FR-009`: System shall inject workflow status UI elements (header controls/status progression) into eligible form views via configuration.
10. `FR-010`: System shall support per-binding enable/disable and rollout scope (company/group/model domain).

### C. Routing, Conditions, and Branching
11. `FR-011`: System shall support sequential and parallel approval steps.
12. `FR-012`: System shall support conditional branches based on record data/context.
13. `FR-013`: System shall support merge semantics after parallel branches (all/any/quorum).
14. `FR-014`: System shall support loop/rework path for “request changes”.
15. `FR-015`: System shall support expression validation and dry-run simulation before publish.

### D. Dynamic Approver Resolution
16. `FR-016`: System shall resolve approvers from direct users, groups, and roles.
17. `FR-017`: System shall resolve approvers from requester hierarchy rules (manager chain).
18. `FR-018`: System shall resolve approvers from record-field references.
19. `FR-019`: System shall support delegate approvers with validity windows.
20. `FR-020`: System shall support anti-self-approval and separation-of-duties constraints.
21. `FR-021`: System shall support quorum/minimum-approver thresholds per step.

### E. Human Task Operations
22. `FR-022`: System shall create actionable approval tasks for each active step.
23. `FR-023`: System shall support approve/reject/request-change actions.
24. `FR-024`: System shall support delegation and reassignment.
25. `FR-025`: System shall support timer-based escalation policies.
26. `FR-026`: System shall support SLA deadlines and overdue states.

### F. Notifications & Integrations
27. `FR-027`: System shall send in-app notifications for assignment, reminders, escalations, and outcomes.
28. `FR-028`: System shall send email notifications using configurable templates per event.
29. `FR-029`: System shall emit signed webhook events for workflow/step/task transitions.
30. `FR-030`: System shall support retry and dead-letter handling for outbound notifications.

### G. BPMN/Decision Support
31. `FR-031`: System shall provide BPMN diagram editing/viewing integration.
32. `FR-032`: System shall support BPMN XML import/export for supported subset.
33. `FR-033`: System shall map BPMN user tasks/gateways/timers/messages to runtime semantics.
34. `FR-034`: System shall expose unsupported BPMN elements as validation errors with remediation hints.
35. `FR-035`: System shall support decision-table-based condition authoring compatibility (DMN-style semantics as requirement level).

### H. Audit, Security, Governance
36. `FR-036`: System shall persist tamper-evident audit entries for all approval actions and config changes.
37. `FR-037`: System shall enforce RBAC for design, publish, approve, administer roles.
38. `FR-038`: System shall enforce admin-only policy for advanced Python snippets.
39. `FR-039`: System shall run Python snippets in restricted sandbox with execution limits and full audit logs.
40. `FR-040`: System shall provide versioned change history and rollback to prior published definitions.

### I. Operations & Monitoring
41. `FR-041`: System shall provide runtime dashboards for active, overdue, failed, and completed workflows.
42. `FR-042`: System shall support incident queue and retry/recover operations.
43. `FR-043`: System shall provide trace view per record (timeline + state transitions).
44. `FR-044`: System shall expose operational metrics and structured logs for observability tooling.

## 5.2 Non-Functional Requirements
1. `NFR-001`: Availability target 99.9% for approval runtime services.
2. `NFR-002`: P95 transition latency under 2 seconds for normal step transitions.
3. `NFR-003`: Horizontal scalability to at least 1k approvals/day baseline with concurrency spikes.
4. `NFR-004`: Strong consistency for approval state transitions on a single record.
5. `NFR-005`: Idempotent handling for repeated triggers/webhook deliveries.
6. `NFR-006`: Complete audit retention policy configurable per compliance needs.
7. `NFR-007`: Multi-company isolation for data, rules, and visibility.
8. `NFR-008`: Backward compatibility for in-flight instances when new versions are published.
9. `NFR-009`: Secure-by-default configuration for expressions and outbound integrations.
10. `NFR-010`: Full timezone-aware SLA/timer behavior.

## 6. Public Interfaces / Types (Requirement-Level Contract)
1. Workflow Definition API contract:
`workflow_definition { id, key, version, status, bpmn_xml, decision_refs, bindings[], publish_meta }`
2. Runtime Instance contract:
`workflow_instance { id, definition_key, definition_version, model, res_id, state, current_nodes[], started_at, completed_at }`
3. Approval Task contract:
`approval_task { id, instance_id, node_id, assignees[], candidates[], status, sla_due_at, escalated }`
4. Event/Webhook contract:
`workflow_event { event_id, event_type, occurred_at, instance_ref, task_ref, actor_ref, payload, signature }`
5. Resolver SPI contract:
`resolve_approvers(context) -> [principal_refs]`
6. Runtime Adapter contract:
`deploy(definition), start(binding_context), signal(instance, event), complete_task(task, decision), get_state(instance)`

## 7. Test Cases and Scenarios
1. Publish validation rejects malformed BPMN subset and invalid condition expressions.
2. Bound action is blocked until required approvals complete.
3. Parallel branch with quorum executes correctly and merges deterministically.
4. Manager-chain resolver updates assignees correctly after org change.
5. Delegation with expiry auto-reverts to original approver.
6. SLA expiry triggers escalation notification and overdue status.
7. Webhook delivery retries on failure and preserves idempotency.
8. Version migration policy keeps in-flight instances on old definition while new starts use new version.
9. Sandbox prevents forbidden operations in Python snippets and logs denial.
10. Incident recovery path unblocks stuck instance without data corruption.

## 8. Multi-Phase Plan With Acceptance Criteria

| Phase | Scope | Acceptance Criteria |
|---|---|---|
| Phase 0 | Requirement baseline and governance ratification | SRS approved by business + architecture + security; all FR/NFR IDs signed off; out-of-scope list accepted |
| Phase 1 | Domain model and contracts | Interface/type contracts finalized; lifecycle/state diagrams approved; validation rules catalog completed |
| Phase 2 | Configuration UX and definition management | Users can create/version/publish definitions from UI; pre-publish validator operational; binding to eligible model actions configurable |
| Phase 3 | Core runtime and approval orchestration | End-to-end execution for sequential/parallel/conditional paths; action gating enforced; deterministic state transitions verified |
| Phase 4 | Human-task operations and notifications | Delegation/escalation/SLA fully functional; in-app + email + webhook events emitted with retries/idempotency |
| Phase 5 | BPMN subset execution and decision compatibility | BPMN subset import/export works; unsupported elements produce explicit validation feedback; decision-table-compatible routing passes scenario tests |
| Phase 6 | Security, audit, observability, readiness | RBAC and sandbox policies enforced; audit completeness verified; incident dashboard/metrics live; load and failover tests meet NFR thresholds |
| Phase 7 | Controlled rollout and adoption | Pilot production rollout succeeds; no critical audit or state-integrity defects; go-live checklist completed for broader deployment |

## 9. Assumptions and Defaults
1. “Any feature” means any model/action that meets eligibility constraints for form/action interception.
2. BPMN execution is subset-based by design; unsupported constructs are explicit, not silent.
3. Advanced Python snippets are allowed only for admins with sandbox and audit.
4. Medium-enterprise performance profile is the planning baseline.
5. Runtime architecture must remain pluggable from first implementation iteration.

## 10. Sources (Concept References)
1. https://docs.camunda.io/docs/components/concepts/workflow-patterns/
2. https://docs.camunda.io/docs/components/modeler/bpmn/user-tasks/
3. https://docs.camunda.io/docs/8.7/components/best-practices/modeling/modeling-beyond-the-happy-path/
4. https://docs.camunda.io/docs/components/concepts/incidents/
5. https://github.com/flowable/flowable-engine
6. https://www.flowable.com/open-source/docs/bpmn/ch05-Introduction/
7. https://docs.temporal.io/
8. https://github.com/temporalio/sdk-python
9. https://docs.conductor-oss.org/
10. https://docs.conductor-oss.org/documentation/configuration/workflowdef/systemtasks/human-task.html
11. https://docs.conductor-oss.org/documentation/configuration/workflowdef/operators/dynamic-fork-task.html
12. https://www.omg.org/spec/BPMN/2.0/
13. https://www.omg.org/spec/DMN/
14. https://bpmn.io/toolkit/bpmn-js/walkthrough
15. https://www.cncf.io/projects/serverless-workflow/
16. https://serverlessworkflow.io/
