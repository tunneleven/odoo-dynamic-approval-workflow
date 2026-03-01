# Dynamic Approval Workflow — Portfolio Glossary

Version: `v1.0`
Date: `2026-03-01`
Owner: Tech Lead
Referenced from: `srs_00_master_traceability.md`

## Purpose
Single source of truth for shared terms used across the SRS portfolio (`SRS-00` through `SRS-10`). All child SRS documents shall use these definitions without local redefinition. New terms must be added here before use in any SRS document.

---

## Terms

### A

**Activation**
The act of making a published definition version eligible to serve new workflow instances within a rollout scope and time window. Activation is an immutable audit event, not a state mutation on the version record. See `SRS-01` §8.

**Archival**
The process of moving terminal/completed runtime records from active storage to long-term storage while preserving audit linkage and evidence references. Archival does not delete data. See `SRS-09` §9.2.

### B

**Backward-compatible (schema change)**
A schema modification that is strictly additive: new optional fields may be added; existing fields may not be removed, renamed, or have their type/semantics changed. Consumers built against the prior minor version shall continue to function without modification. See `SRS-10` §8.1.

**Binding**
A configuration record that links a workflow definition to a specific business model, action method, and enforcement mode. Bindings control when and how workflow gating is applied. See `SRS-02` §5.

**Bounded (TTL/backoff/window)**
A numeric parameter with explicit minimum and maximum values defined in the owning SRS section. "Bounded" without accompanying numeric limits is prohibited.

### C

**Callback**
A post-approval action that executes a target business method (e.g., `sale.order.action_confirm`) upon terminal approval. Callback execution is governed by idempotency, execution principal, and failure recovery policies. See `SRS-02` §11.

**Canonical XML**
The normalized, deterministic BPMN XML representation that serves as the single source of truth for workflow process structure. All compile artifacts and runtime metadata derive from canonical XML. See `SRS-03` §8.

**Compliance-critical**
A binding-level flag indicating the workflow is subject to regulatory or compliance requirements. Compliance-critical bindings prohibit `ui_only` enforcement mode and `gate_exception` policies. See `SRS-02` §6.1.

**Correlation ID**
A globally unique identifier propagated across all operations within a workflow instance lifecycle for end-to-end observability tracing. See `SRS-10` §7.3.

### D

**Dead-letter queue (DLQ)**
A holding queue for outbound webhook events that have exhausted all retry attempts. Events in DLQ require operator intervention for controlled replay. See `SRS-08` §8.2.

**Downgraded (follower)**
A follower subscription narrowed to read-only notifications only (outcome summary); assignment, reminder, and escalation notifications are suppressed. See `SRS-05` §10.2.

### E

**Effectively-once (canonical term)**
The idempotency guarantee for mutating runtime adapter operations: under at-least-once delivery conditions, a valid `idempotency_key` ensures that the mutation produces its effect exactly once — duplicate calls return the original outcome without creating additional side effects. This is the portfolio-standard term; "exactly-once" shall not be used as it implies network-level guarantees beyond module control. See `SRS-10` DFR-10-001, `SRS-02` §11.5.

> **NOTE:** "Exactly-once" appearing in any SRS document is a terminology error and shall be corrected to "effectively-once."

**Enforcement mode**
The mechanism by which a binding gates a business action. Valid modes: `orm_enforced` (server-side interception), `hybrid` (server + UI), `ui_only` (client-side only). See `SRS-02` §6.1.

**Escalation**
The process triggered when a task breaches its SLA deadline. Escalation resolves a new target (via the same identity validation rules as initial resolution) and creates an escalation event. See `SRS-05` §8.3.

### F

**Fail-closed**
Default failure behavior for `orm_enforced` and `hybrid` enforcement modes: if the gate evaluation or interceptor fails, the action is blocked (not allowed). See `SRS-02` §7.6.

**Fallback source**
An alternative approver resolution source evaluated when the primary resolved set is empty. Valid types: `fallback_group`, `fallback_hierarchy_level`, `fallback_named_users`, `fallback_escalation_target`. See `SRS-05` §6.3.

### G

**Gate / Gating**
The enforcement mechanism that blocks a business action until required approvals are satisfied. Gate states: `blocked`, `allowed`, `allowed_with_warning`. See `SRS-02` §8.

**Grant (temporary access)**
A time-bounded, least-privilege access record created automatically for approvers to enable task execution. Grants have explicit TTL (5 min–72 hours, default 24 hours). See `SRS-07` §7.

### I

**Idempotency key**
A client-supplied unique identifier for mutating operations. The key scope is `(operation_type, operation_subject_ref, idempotency_key)`. See `SRS-10` §7.1.

**Incident**
A system-created operational record for failures requiring operator attention (callback failures, gate ambiguity, approver resolution failures, sandbox violations, etc.). Incidents have a lifecycle: `open` → `triaged` → `retry_scheduled` / `resolved` / `closed_with_exception`. See `SRS-09` §7.

### L

**Legal hold**
An override flag on records that prevents archival or purge regardless of retention profile duration, until the hold is explicitly released by authorized governance action. See `SRS-09` §9.3, `SRS-06` §9.

### P

**Policy calendar**
A configuration defining working hours, working days, and holidays per company or group scope. Used for SLA and reminder calculations. Default when unconfigured: 24/7 UTC (elapsed-time mode). See `SRS-05` §8.3.

**Published (definition status)**
A definition version status indicating the version has passed validation and is eligible for activation. Only `published` versions can serve new instances. See `SRS-01` §6.

**Purge**
The irreversible deletion of archived runtime data after retention period expiry. Purge requires authorization, excludes legal-hold records, and produces an immutable purge report. See `SRS-09` §9.3.

### R

**Replay window**
The time window (default 300 seconds) within which a webhook consumer accepts event timestamps as fresh. Events outside this window are rejected. See `SRS-08` §7.3.

**Retention profile**
A named policy controlling how long runtime data is retained before archival/purge eligibility. Standard profiles: `short_term` (90 days), `standard` (365 days), `compliance_extended` (7 years). See `SRS-09` §9.1.

**Rollout scope**
The applicability boundary for a binding or activation: `company`, `group`, or `global`. Higher specificity takes precedence. See `SRS-02` §9.

### S

**Separation-of-duty (SoD)**
A policy constraint that prevents prohibited combinations of actor, role, or prior action within a single workflow instance. See `SRS-05` §7.3.

**Standard-size flow**
A BPMN diagram with at most 75 total BPMN nodes (tasks, gateways, events, intermediate elements). Used as the performance benchmark threshold for NFR-009. See `SRS-03` §9.4.

**System attestation**
An evidence artifact created by a dedicated non-human signer identity when timeout `auto-approve` is triggered on a `sign_required` step. Must be explicitly enabled per step and clearly labeled as non-human. See `SRS-06` §6, §7.

### T

**Terminal state**
An instance or task state from which no further transitions are possible (e.g., `approved`, `rejected`, `cancelled`). Terminal transitions trigger callbacks and evidence finalization. See `SRS-04` §5.2.

---

## Usage Rules
1. New shared terms must be added to this glossary before first use in any SRS document.
2. Local redefinition of glossary terms in child SRS documents is prohibited.
3. Glossary updates require version increment and Tech Lead approval.
4. Terms marked with specific SRS references indicate the authoritative detail source.
