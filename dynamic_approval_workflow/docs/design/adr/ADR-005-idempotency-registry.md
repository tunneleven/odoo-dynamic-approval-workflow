# ADR-005: Dedicated Idempotency Registry Model

**Status:** Accepted  
**Date:** 2026-03-01  
**Decision Makers:** Tech Lead  
**SDS Reference:** §10 Idempotency Pattern

---

## Context

The SRS requires exactly-once semantics for mutating runtime adapter operations when a valid `idempotency_key` is provided (NFR-016, SRS-10 §6–7). The key uniqueness scope is `(operation_type, operation_subject_ref, idempotency_key)`.

Three storage approaches were evaluated:

1. **Dedicated model** — `workflow.idempotency.registry` with a single table for all idempotent operations.
2. **Field on each model** — add `idempotency_key` column to `workflow.instance`, `workflow.task`, etc.
3. **PostgreSQL advisory locks + transient table** — use `pg_advisory_lock` for mutex and a transient log for dedup.

## Decision

**Option 1: Dedicated model `workflow.idempotency.registry`.**

A single model stores all idempotency outcomes keyed by `operation_scope_hash = SHA-256(operation_type, operation_subject_ref, idempotency_key)`. The model has a `UNIQUE` constraint on `operation_scope_hash`.

## Rationale

### Why dedicated model?

1. **Clean separation**: Idempotency is a cross-cutting concern. Embedding it into domain models (instance, task, binding) scatters the logic across 6+ models and mixes operational state with deduplication metadata.
2. **Single query path**: All idempotency checks use the same table, same index, same code path. Easy to reason about, test, and optimize.
3. **Easy retention**: The registry has an `expires_at_utc` field. A single cron job can purge expired entries without touching domain models.
4. **Audit-friendly**: Correlation and causation IDs are stored alongside the idempotency record, enabling end-to-end trace reconstruction from a single table.
5. **Conflict detection**: When a duplicate key arrives with a different payload, the registry detects the conflict by comparing `payload_hash`. This is impossible with a simple field on the domain model (which stores only the key, not the payload hash).

### Why not field on each model?

- Adds `idempotency_key` to 6+ models, each needing its own uniqueness check and conflict detection logic.
- Retention/purge would need to iterate over multiple tables.
- Correlation/causation would need additional fields on each model.
- Callback idempotency (SRS-02 §11.5) crosses model boundaries — can't store it on a single domain model.

### Why not advisory locks?

- `pg_advisory_lock` provides mutex but not deduplication persistence. If a process crashes after acquiring the lock but before writing the result, there's no record of the attempt.
- Advisory locks have no built-in TTL — would need custom cleanup.
- Not auditable — no persistent record of which operations were idempotency-protected.

## Implementation Contract

### Model Fields

| Field | Type | Purpose |
|---|---|---|
| `operation_type` | `Selection` | Operation category |
| `operation_subject_ref` | `Char` | Target record reference |
| `idempotency_key` | `Char(128)` | Client-supplied key |
| `operation_scope_hash` | `Char(64)` | SHA-256 scope hash (UNIQUE) |
| `payload_hash` | `Char(64)` | SHA-256 of request payload |
| `result_status` | `Selection` | `success`, `conflict`, `error` |
| `result_ref` | `Char` | Outcome record reference |
| `correlation_id` | `Char(64)` | Trace ID |
| `causation_id` | `Char(64)` | Parent operation ID |
| `created_at_utc` | `Datetime` | Creation timestamp |
| `expires_at_utc` | `Datetime` | Retention expiry |

### SQL Constraint

```sql
UNIQUE(operation_scope_hash)
```

### Check Flow

```
1. Compute scope_hash = SHA-256(type + subject_ref + key)
2. Compute payload_hash = SHA-256(canonical_payload)
3. Attempt INSERT (scope_hash, payload_hash, ...)
4. If OK → proceed with operation → UPDATE result on completion
5. If UNIQUE violation:
   a. payload_hash matches stored → return stored result_ref (replay)
   b. payload_hash differs → return idempotency_conflict error
```

### Retention

- `expires_at_utc` set based on retention policy (interim default: 90 days, OI-23).
- Cron job purges expired entries.
- Purge is safe — expired entries have already served their dedup purpose.

### Covered Operations

Per SRS-10 §6.1:
- `start`, `signal`, `complete_task`, `cancel_instance`, `reassign_task`, `execute_callback`
- Read operations (`get_instance_state`, `get_gate_state`) are excluded — they don't mutate state.

## Consequences

### Positive
- Single table, single index, single code path for all idempotency checks.
- Clean retention via `expires_at_utc` + cron purge.
- Full correlation chain in one model.
- Conflict detection via `payload_hash` comparison.

### Negative
- Adds one model (~1 table) to the database. For 1k approvals/day, this produces ~5–10k rows/day across operation types. At 90-day retention: ~450k–900k rows. Well within PostgreSQL's capability with proper indexing.
- INSERT-on-conflict path requires careful error handling to distinguish UNIQUE violation from other database errors.

### Mitigation
- Index on `operation_scope_hash` (UNIQUE) covers the primary lookup.
- Optional index on `expires_at_utc` for purge queries.
- INSERT uses `try/except IntegrityError` with savepoint to handle UNIQUE conflicts within the ORM transaction.

## Alternatives Considered

| Option | Separation | Conflict Detection | Retention | Complexity | Verdict |
|---|---|---|---|---|---|
| Dedicated model | Clean | Full (payload_hash) | Simple | Low | **Accepted** |
| Field per model | Scattered | Partial | Complex | Medium | Rejected |
| Advisory locks | N/A | None | N/A | High | Rejected |

## References

- SRS-10 §6–7 (runtime adapter operations, idempotency contract)
- SRS-02 §11.5 (callback idempotency)
- NFR-016 (exactly-once semantics)
- Parent SRS §8.2 (idempotency requirements)
- OI-23 (retention window duration — pending resolution)
