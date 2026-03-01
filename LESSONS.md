# LESSONS.md — Mistakes and Preventions

> Shared log for AI agents and human developers.
> Read this file before starting any implementation task.
> Append new entries when a mistake requires > 1 fix attempt.
>
> Format: sequential LESSON-XXX entries. Never delete or reorder existing entries.

---

## How to Use

**Before coding:** Read all entries below. Check if your current task matches any past mistake pattern.

**After a mistake:** Append a new entry using this template:

```markdown
### LESSON-XXX: Short descriptive title
- **Date:** YYYY-MM-DD
- **Task:** TASK-XXX (or free description)
- **Symptom:** What went wrong (error message, test failure, review rejection)
- **Root cause:** Why it happened (missing context, wrong assumption, doc gap)
- **Fix:** What was changed to resolve it
- **Prevention rule:** Concrete rule to prevent recurrence (add to AGENTS.md if systemic)
```

---

## Entries

### LESSON-001: SDS v0.2 had wrong module count — architecture drift
- **Date:** 2026-03-01
- **Task:** SDS authoring
- **Symptom:** SDS v0.2 specified 6 modules; stakeholder decision was 3 modules
- **Root cause:** SDS was drafted before ADR decisions were finalized. No gate check between draft and ADR approval.
- **Fix:** Rewrote SDS v1.0 with correct 3-module architecture after ADR-001 approval
- **Prevention rule:** Never draft implementation specs before architecture decisions are locked via ADR. SDS sections that reference ADRs must include the ADR file path as a cross-reference.

### LESSON-002: SDS v0.2 specified cron-only scheduling — missed queue_job requirement
- **Date:** 2026-03-01
- **Task:** SDS §6 Runtime Engine
- **Symptom:** SDS §16 binding constraint said "must not introduce queue-framework dependency" — contradicted by stakeholder decision to use hybrid cron + queue_job
- **Root cause:** Constraint was written before ADR-004 decision. No invalidation check when new ADRs landed.
- **Fix:** Updated SDS §6 with hybrid scheduler architecture and added `queue_job` to dependency list
- **Prevention rule:** When a new ADR is accepted, scan all SDS binding constraints for contradictions. ADR decisions supersede pre-ADR constraints.

### LESSON-003: Duplicate section numbering after SDS edit
- **Date:** 2026-03-01
- **Task:** SDS restructuring
- **Symptom:** Sections §15-18 appeared twice — old and new sections had same numbers
- **Root cause:** Inserted new sections (Security, File Structure, Performance) before the tail sections without renumbering
- **Fix:** Renumbered tail sections §16→§19, §17→§20, §18→§21, added §22 Traceability, §23 Sign-off
- **Prevention rule:** After inserting sections into a numbered document, always verify the full heading sequence with `grep '^## ' <file>` before committing.

---

<!-- Append new lessons above this line -->
