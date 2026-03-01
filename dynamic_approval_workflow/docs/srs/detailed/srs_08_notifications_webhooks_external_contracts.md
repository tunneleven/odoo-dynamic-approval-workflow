# SRS-08 Notifications, Webhooks, and External Contracts

Version: `v1.2-draft`
Date: `2026-03-01`
Parent: `dynamic_approval_workflow_srs_v1.3.md`
Master Traceability: `srs_00_master_traceability.md`

## 1. Purpose
Define detailed requirements for in-app/email notifications, outbound webhook contracts, signature verification rules, delivery retry and DLQ behavior, and consumer idempotency safety.

## 2. Scope
In scope:
1. Notification events for assignment/reminders/escalation/outcomes.
2. Configurable email template dispatch for key workflow events.
3. Signed webhook lifecycle transition events.
4. Retry and dead-letter behavior for outbound failures.
5. Idempotency-safe delivery contract for webhook consumers.
6. HMAC-SHA256 signature format and replay-window validation contract.

Out of scope:
1. Core task state transition logic (`SRS-05`).
2. Incident queue operations ownership (`SRS-09`).
3. Data schema evolution governance (`SRS-10`).

## 3. Inherited Requirement Coverage
- FR: `FR-056..060`, `FR-083`
- NFR: `NFR-005`

## 4. Decomposed Detailed Requirements (DFR)
| DFR ID | Statement | Maps To |
|---|---|---|
| `DFR-08-001` | In-app notifications shall be sent for assignment, reminders, escalation, and outcomes. | `FR-056` |
| `DFR-08-002` | Email notifications shall support configurable templates per key event type. | `FR-057` |
| `DFR-08-003` | Lifecycle transition events shall be emitted via signed webhooks. | `FR-058` |
| `DFR-08-004` | Outbound webhook delivery shall support retry policy and dead-letter handling. | `FR-059` |
| `DFR-08-005` | Webhook payloads and delivery semantics shall be idempotency-safe for consumers. | `FR-060`, `NFR-005` |
| `DFR-08-006` | Webhook signatures shall use HMAC-SHA256 with per-endpoint secret, timestamp header, and replay-window validation contract. | `FR-083` |

## 5. Domain Objects (Conceptual)
1. `workflow.notification_event`
- Internal normalized notification event instance.
2. `workflow.notification_template`
- Configurable channel templates.
3. `workflow.outbound_webhook_endpoint`
- Endpoint config with secret and policy.
4. `workflow.outbound_delivery_attempt`
- Delivery attempt record for retry and observability.
5. `workflow.outbound_dead_letter`
- Terminal failed events requiring operator action.

## 6. Notification Contract
### 6.1 Event Matrix
1. Assignment -> in-app + optional email.
2. Reminder -> in-app + optional email.
3. Escalation -> in-app + optional email.
4. Outcome (approved/rejected/cancelled) -> in-app + optional email.

### 6.2 Template Rules
1. Email template is selectable by event type and binding scope.
2. Missing template falls back to default template if configured.
3. Template render failures create notification incident and do not block workflow transition commit.

### 6.3 Delivery Ordering
1. In-app notification commit is in same transactional boundary as event enqueue.
2. Email/webhook dispatch is asynchronous via outbound queue.

## 7. Webhook Contract
### 7.1 Event Envelope
1. `event_id` (unique immutable ID)
2. `event_type`
3. `occurred_at_utc`
4. `producer`
5. `tenant_context`
6. `idempotency_key`
7. `payload`

### 7.2 Signature Headers (`FR-083`)
1. `X-Workflow-Signature` (HMAC-SHA256 digest over canonical payload and timestamp string)
2. `X-Workflow-Timestamp` (UTC epoch seconds)
3. `X-Workflow-Event-Id` (matches envelope `event_id`)

### 7.3 Replay Window Contract
1. Consumer validates timestamp freshness within configured replay window (default: 300 seconds).
2. Events outside replay window must be rejected by consumer contract.
3. Producer and consumer clocks shall be synchronized within 30-second operational tolerance; drift exceeding this threshold shall trigger a clock-drift incident.

### 7.4 Secret Management
1. Signature secret is per endpoint.
2. Secret rotation supports overlap period (minimum 1 hour, maximum 24 hours) with dual validation keys.
3. Secret exposure incident requires endpoint suspension and key rotation.

## 8. Retry and Dead-Letter Contract
### 8.1 Retry Policy
1. Retries use bounded exponential backoff with base interval 5 seconds and cap at 5 minutes.
2. Maximum retry attempts per delivery: 5.
3. Retry classification is based on the response classification matrix below.
4. Non-retryable errors route directly to DLQ.

### 8.1a Retry Classification Matrix
| Category | HTTP Status / Condition | Retryable | Action |
|---|---|---|---|
| Transient server error | `500`, `502`, `503`, `504` | Yes | Retry with backoff |
| Rate limited | `429` | Yes | Retry after `Retry-After` header or default backoff |
| Network failure | Connection timeout, DNS failure, TCP reset | Yes | Retry with backoff |
| Client error | `400`, `401`, `403`, `404`, `405`, `422` | No | Route to DLQ immediately |
| Redirect | `301`, `302`, `307`, `308` | No | Route to DLQ (endpoint config must be updated) |
| Success | `200`, `201`, `202`, `204` | N/A | Delivery confirmed |
| Unknown / unparseable | Non-HTTP or malformed response | Yes (1 retry only) | If retry fails, route to DLQ with `unknown_response` |

### 8.2 Dead-Letter Handling
1. After max attempts, event moves to dead-letter queue.
2. DLQ entry includes endpoint, event metadata, last error, and attempt history.
3. Operators can perform controlled replay from DLQ with idempotency safeguards.

### 8.3 Deterministic Replay Behavior
1. Replay preserves original `event_id` and `idempotency_key`.
2. Replay increments delivery attempt metadata only.

## 9. Consumer Idempotency Contract (`FR-060`, `NFR-005`)
1. Consumers should treat `idempotency_key` as idempotent mutation key.
2. Duplicate deliveries with same `idempotency_key` are expected and must be safe.
3. Same key with semantically different payload is producer error and incident trigger.

## 10. APIs and Events (Outbound Domain)
### 10.1 Logical Operations
1. `enqueue_notification_event(event)`
2. `render_notification_template(template_id, context)`
3. `dispatch_in_app_notification(event_id)`
4. `dispatch_email_notification(event_id)`
5. `dispatch_webhook_event(endpoint_id, event_id)`
6. `retry_webhook_delivery(delivery_id)`
7. `replay_dead_letter(dlq_id, actor)`

### 10.2 Required Audit Events
1. `workflow.notify.in_app_dispatched`
2. `workflow.notify.email_dispatched`
3. `workflow.notify.template_render_failed`
4. `workflow.webhook.dispatched`
5. `workflow.webhook.retry_scheduled`
6. `workflow.webhook.dead_lettered`
7. `workflow.webhook.dead_letter_replayed`
8. `workflow.webhook.signature_rotated`

## 11. Acceptance Criteria and Test Scenarios
| Test ID | Requirement IDs | Scenario | Expected Result |
|---|---|---|---|
| `TC-FR-056-001` | `FR-056` | Trigger assignment/reminder/escalation/outcome events | In-app notifications emitted for each configured event |
| `TC-FR-057-001` | `FR-057` | Render and send configured email template for outcome event | Email delivered with correct template |
| `TC-FR-058-001` | `FR-058` | Emit lifecycle transition webhook | Signed webhook event dispatched |
| `TC-FR-059-001` | `FR-059` | Webhook endpoint returns transient failure | Retry scheduled per policy |
| `TC-FR-059-002` | `FR-059` | Webhook endpoint keeps failing beyond max attempts | Event moved to DLQ |
| `TC-FR-060-001` | `FR-060`, `NFR-005` | Deliver duplicate webhook with same idempotency key | Consumer-safe duplicate behavior contract maintained |
| `TC-FR-083-001` | `FR-083` | Verify webhook signature headers and replay window rules | Signature and timestamp contract satisfied |
| `TC-NFR-005-001` | `NFR-005` | Replay dead-letter event | No duplicate mutation effect expected for consumer |
| `TC-FR-083-002` | `FR-083` | Validate dual-key overlap during secret rotation | Old/new signatures accepted during overlap only |
| `TC-FR-057-002` | `FR-057` | Template render failure on email channel | Incident logged; workflow transition remains committed |
| `TC-FR-083-003` | `FR-083` | Producer clock skew exceeds 30s tolerance | Delivery flagged; clock-drift incident raised |
| `TC-FR-083-004` | `FR-083` | Secret rotated while retries in-flight | Retry uses active dual-key set; delivery remains verifiable |
| `TC-NFR-005-002` | `NFR-005` | DLQ replay invoked twice by operator | Idempotency key prevents duplicate consumer effect |

## 12. Traceability Matrix
| Canonical ID | Covered Sections | Primary Tests |
|---|---|---|
| `FR-056` | 4, 6 | `TC-FR-056-001` |
| `FR-057` | 4, 6 | `TC-FR-057-001`, `TC-FR-057-002` |
| `FR-058` | 4, 7 | `TC-FR-058-001` |
| `FR-059` | 4, 8 | `TC-FR-059-001`, `TC-FR-059-002` |
| `FR-060` | 4, 9 | `TC-FR-060-001`, `TC-NFR-005-001` |
| `FR-083` | 4, 7 | `TC-FR-083-001`, `TC-FR-083-002` |
| `NFR-005` | 4, 9 | `TC-NFR-005-001`, `TC-FR-060-001` |

## 13. Edge Case Register
| Edge Case ID | Edge Case | Expected Behavior | Owner | Linked Test ID |
|---|---|---|---|---|
| `EC-08-01` | Producer clock skew causes timestamp outside replay window | Delivery flagged and incident raised for clock drift policy breach | Ops Lead | `TC-FR-083-003` |
| `EC-08-02` | Endpoint secret rotated while retries in-flight | Retry uses active key set and remains verifiable | Integration Lead | `TC-FR-083-004` |
| `EC-08-03` | DLQ replay invoked twice by operators | Idempotency key prevents duplicate consumer effect | Workflow Admin | `TC-NFR-005-002` |

## 14. Sign-off Checklist
1. All inherited requirements in Section 3 are mapped in Section 12.
2. Signature and replay-window headers are explicitly specified.
3. Retry and DLQ semantics are deterministic and auditable.
4. Idempotency consumer contract is explicit and testable.
5. Template failure semantics do not violate runtime consistency guarantees.

## 15. Open Issues
1. ~~Final response-code retry classification matrix~~ — **RESOLVED**: defined in §8.1a.
2. ~~Clock synchronization operational threshold~~ — **RESOLVED**: defined as 30-second tolerance in §7.3.

## 16. Next Document
After approval of `SRS-08`, proceed to `srs_09_operations_monitoring_retention_reliability.md`.
