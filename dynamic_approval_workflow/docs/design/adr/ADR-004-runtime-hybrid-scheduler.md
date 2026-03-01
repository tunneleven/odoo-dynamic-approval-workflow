# ADR-004: Runtime Hybrid Scheduler (ir.cron + queue_job)

**Status:** Accepted  
**Date:** 2026-03-01  
**Decision Makers:** Tech Lead  
**SDS Reference:** §6 Runtime Engine Design

---

## Context

The workflow runtime requires two classes of scheduled work:

1. **Periodic scanning** — discover expired timers, approaching SLA deadlines, orphan access grants.
2. **Async execution** — deliver notifications, dispatch webhooks, execute post-approval callbacks, fire timer actions.

Three scheduling mechanisms were evaluated.

## Decision

**Hybrid: ir.cron for periodic scanning + OCA queue_job for async execution.**

Cron discovers work items on fixed intervals. Each discovered item is dispatched as a `queue_job` task for reliable async execution with retry and dead-letter semantics.

## Rationale

### Why not cron-only?

| Concern | Cron-only | Hybrid |
|---|---|---|
| Timer execution latency | Bounded by cron interval (1–5 min) | queue_job processes immediately after discovery |
| Retry semantics | Must implement custom retry in cron method | queue_job has built-in retry with configurable backoff |
| Dead-letter handling | Must implement custom DLQ | queue_job has built-in failure channels |
| Callback isolation | Callback failure in cron blocks the batch | Each callback is a separate job — failures are isolated |
| Concurrency | One cron worker processes all items sequentially | queue_job workers process items in parallel |

### Why not queue_job-only?

- `queue_job` is event-driven — it doesn't have a built-in "scan every 5 minutes" mode.
- SLA checks and orphan grant reconciliation are inherently polling tasks. Using queue_job for these would require a "scheduler job" that enqueues scanning jobs — adding unnecessary indirection.
- `ir.cron` is Odoo-native, zero-dependency for scanning. Adding queue_job as the sole scheduler would make the entire system depend on the queue_job worker process being up.

### Why hybrid is the best fit

Cron provides reliable, Odoo-native periodic scanning that works even if queue_job workers are temporarily down. queue_job provides reliable, retry-capable async execution with proper failure isolation. The combination gives:

- **Discovery** → predictable, bounded, Odoo-native.
- **Execution** → immediate, parallel, retry-capable, failure-isolated.

### queue_job as OCA dependency

`queue_job` is a mature OCA module (10+ years, actively maintained). It:
- Uses PostgreSQL advisory locks for job coordination.
- Has configurable channels, retry, and priority.
- Integrates with Odoo's transaction model (jobs created in-transaction, dispatched post-commit).
- Is widely used in production OCA deployments.

The dependency adds one external addon but eliminates the need to build custom retry, DLQ, and parallel execution infrastructure.

## Implementation Contract

### Cron Jobs (Discovery)

| Cron | Model | Method | Interval | Purpose |
|---|---|---|---|---|
| Timer discovery | `workflow.node.runtime` | `_cron_fire_timers` | 1 minute | Find expired timers → enqueue timer action jobs |
| SLA checker | `workflow.task` | `_cron_check_sla` | 5 minutes | Find approaching/breached SLAs → enqueue notification jobs |
| Grant reconciler | `workflow.access.grant` | `_cron_reconcile_orphan_grants` | 1 hour | Find orphan grants → revoke |
| Deadline checker | `workflow.task` | `_cron_check_deadlines` | 5 minutes | Find approaching deadlines → enqueue reminder jobs |

### queue_job Tasks (Execution)

| Job | Model | Method | Retry Policy | On Exhaustion |
|---|---|---|---|---|
| Timer action | `workflow.node.runtime` | `_job_execute_timer_action` | 3 retries: 1s, 5s, 30s | Create incident |
| Callback | `workflow.binding` | `_job_execute_callback` | 3 retries: 5s, 30s, 120s | Create incident |
| Webhook | `workflow.outbound.event` | `_job_dispatch_webhook` | 5 retries: 5s, 15s, 60s, 300s, 300s | Dead-letter queue |
| Notification | `workflow.notification.log` | `_job_send_notification` | 3 retries: 5s, 30s, 120s | Log warning + incident |

### Post-Commit Dispatch Pattern

```python
def _complete_task(self, outcome, evidence=None):
    # ... synchronous tick logic (within transaction) ...

    # Post-commit: enqueue async work
    self.env.cr.postcommit.add(
        lambda: self.with_delay()._job_send_notification(task_id)
    )
    self.env.cr.postcommit.add(
        lambda: self.with_delay()._job_execute_callback(instance_id, binding_id)
    )
```

This ensures async work is only dispatched after the transaction commits successfully.

### Concurrency

- Each queue_job task acquires per-instance advisory lock before any mutation.
- Timer discovery cron uses `SELECT ... FOR UPDATE SKIP LOCKED` to avoid processing items already being handled.
- Multiple queue_job workers can process jobs in parallel without conflicts.

## Consequences

### Positive
- Reliable retry and dead-letter semantics without custom infrastructure.
- Failure isolation — one failed callback doesn't block other workflows.
- Parallel execution via queue_job workers.
- SLA/timer scanning is predictable and Odoo-native.

### Negative
- Adds `queue_job` as external OCA dependency.
- Requires queue_job worker process to be running (`odoo-bin --workers=N` or `queue_job_cron_jobrunner`).
- Two scheduling mechanisms to understand and maintain.

### Mitigation
- Document queue_job setup in deployment guide.
- Monitor queue_job health via operations dashboard.
- If queue_job is temporarily down, cron scanning still detects overdue items — they are processed when workers resume.

## Alternatives Considered

| Option | Scanning | Execution | Retry | Dependency | Verdict |
|---|---|---|---|---|---|
| ir.cron only | Native | Serial, manual retry | Custom | None | Rejected |
| queue_job only | Needs workaround | Parallel, built-in retry | Built-in | OCA | Rejected |
| Hybrid | Native | Parallel, built-in retry | Built-in | OCA | **Accepted** |

## References

- SRS-04 §6.2 (deterministic runtime tick)
- SRS-04 §9 (timeout auto-decision)
- SRS-04 §12.4 (concurrency control)
- SRS-08 (notifications, webhooks)
- SRS-02 §11 (callback execution)
- NFR-002 (< 2s transition latency)
- OCA queue_job: `https://github.com/OCA/queue/tree/19.0/queue_job`
