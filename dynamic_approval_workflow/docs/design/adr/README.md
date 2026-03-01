# ADR Index — Dynamic Approval Workflow

Architecture Decision Records referenced by `sds_dynamic_approval_workflow.md` v1.0.

## Accepted ADRs

| ADR | Title | Status | SDS Section |
|---|---|---|---|
| [ADR-001](ADR-001-three-module-architecture.md) | Three-Module Architecture | Accepted | §3 |
| [ADR-002](ADR-002-full-patch-method-enforcement.md) | Full `_patch_method` Enforcement | Accepted | §7 |
| [ADR-003](ADR-003-bpmn-owl-lazy-loading.md) | bpmn-js OWL Lazy Loading | Accepted | §5 |
| [ADR-004](ADR-004-runtime-hybrid-scheduler.md) | Runtime Hybrid Scheduler (cron + queue_job) | Accepted | §6 |
| [ADR-005](ADR-005-idempotency-registry.md) | Dedicated Idempotency Registry | Accepted | §10 |

## Naming Convention

`ADR-<NNN>-<short-topic>.md`

## Template

```markdown
# ADR-XXX: <Title>

Date: YYYY-MM-DD
Status: Proposed | Accepted | Superseded

## Context
What problem/constraint is being addressed?

## Decision
What was decided?

## Alternatives Considered
1. Option A
2. Option B

## Consequences
Trade-offs and follow-on impacts.

## Traceability
- DFR IDs:
- FR/NFR IDs:
- SDS Section:
```
