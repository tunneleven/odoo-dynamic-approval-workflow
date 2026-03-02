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

### LESSON-005: Odoo 19 migration errors require repo-wide compatibility guard
- **Date:** 2026-03-01
- **Task:** TASK-P1-001
- **Symptom:** Additional Odoo 19 install failures surfaced after the `res.groups.category_id` fix (`ir.cron.numbercall`, search view `group expand`, mixed-model inherited view).
- **Root cause:** Legacy snippets from pre-19 patterns were still present in module XML and in design docs, and there was no automated guard in CI.
- **Fix:** Removed incompatible XML fields/attributes, corrected inherited view model mismatch, migrated `_sql_constraints` usages to `models.Constraint(...)`, and added `scripts/check_odoo19_compat.py` + `.github/workflows/odoo19-compat-guard.yml`.
- **Prevention rule:** Every PR touching XML must pass Odoo 19 compatibility guard; never copy snippets without validating fields/attributes against local Odoo 19 source models.

### LESSON-004: Odoo 19 security groups use `privilege_id`, not `category_id`
- **Date:** 2026-03-01
- **Task:** TASK-P1-001
- **Symptom:** Module install failed with `ValueError: Invalid field 'category_id' in 'res.groups'`.
- **Root cause:** Security XML used pre-19 `res.groups` schema and assigned `category_id` directly on groups.
- **Fix:** Migrated group definitions to Odoo 19 pattern: create `res.groups.privilege` linked to `ir.module.category` and set `privilege_id` on all workflow groups. Updated OMB-03 and agent instructions to enforce this rule.
- **Prevention rule:** Before coding security XML, validate target model fields against local Odoo source (`odoo/addons/base/models/res_groups.py`) and reject any snippet that sets `category_id` on `res.groups`.

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

### LESSON-012: Cron template in codegen instructions still had `numbercall`
- **Date:** 2026-03-02
- **Task:** Template audit
- **Symptom:** `copilot-codegeneration-instructions.md` cron template emitted `<field name="numbercall">-1</field>`, which is removed in Odoo 19 and causes install failures.
- **Root cause:** Template was copied from pre-19 code and never updated after LESSON-004/005 added the cron guard to AGENTS.md.
- **Fix:** Removed `numbercall` from the cron template in `copilot-codegeneration-instructions.md`.
- **Prevention rule:** Any template block (cron, model, view) in codegen instructions must be validated against Odoo 19 source before committing. Templates are authoritative — if they have a bug, every generated file inherits it. Review templates whenever a new Odoo 19 compat lesson is added.

### LESSON-011: `unlink()` used Python `filtered()` for existence check — should use `search_count()`
- **Date:** 2026-03-02
- **Task:** TASK-P1-002 (PR review)
- **Symptom:** `unlink()` fetched all version records via `record.version_ids.filtered(...)` to check if any published version exists, loading full ORM records unnecessarily.
- **Root cause:** Agent wrote defensive code using Python-side filtering instead of a DB-side aggregate query.
- **Fix:** Replaced with `self.env["..."].search_count([...])` using `self.ids` — single DB query, no record loading.
- **Prevention rule:** For existence checks in `unlink()` / `write()` guards on related records: use `search_count()` with `('relation_field', 'in', self.ids)`, never `recordset.filtered()`. Use `filtered()` only when records are already loaded in memory for another reason.

### LESSON-010: `_compute_name` using `record.id or 'new'` — compute does not run again after create with real ID
- **Date:** 2026-03-02
- **Task:** TASK-P1-007 (PR review)
- **Symptom:** `_compute_name` produced `INC-new [category]` and never updated to `INC-<id> [category]` because stored compute only triggers on dependency field changes, not on ID assignment.
- **Root cause:** `record.id` is `None` during compute at create time; no dependency triggers recompute after actual ID is assigned.
- **Fix:** Added `create()` override to assign `record.name` after `super().create()` returns, ensuring the real ID is used.
- **Prevention rule:** When a model's name pattern includes the database ID (e.g., `INC-{id}`), you MUST override `create()` to set it post-insert. Computed fields with `store=True` cannot use `record.id` reliably in newrecord context.

### LESSON-009: `action_*` methods had optional `note=None` parameter — violates OMB API contract
- **Date:** 2026-03-02
- **Task:** TASK-P1-007 (PR review)
- **Symptom:** `action_resolve(note=None)` and `action_close_with_exception(note=None)` accepted an inline `note` param; OMB specifies no params — note is read from the stored `resolution_note` field.
- **Root cause:** Agent added convenience param without checking OMB API contract; wizard-less approach but wrong mechanism.
- **Fix:** Removed note params; methods read directly from `record.resolution_note`.
- **Prevention rule:** Button action methods (`action_*`) must match the OMB signature exactly — zero params unless OMB specifies otherwise. Notes, config, or context should come from stored fields, not method params. Check OMB before adding any param.

### LESSON-008: `action_retry` accepted `'open'` state — OMB state machine said `'triaged'` only
- **Date:** 2026-03-02
- **Task:** TASK-P1-007 (PR review)
- **Symptom:** Guard `if record.state not in ("open", "triaged")` allowed retrying open incidents, but OMB-02 §6.1 defines retry as triaged-only.
- **Root cause:** State machine was implemented from memory/assumption, not from OMB definition.
- **Fix:** Changed guard to `if record.state != "triaged"` and updated button `invisible` attr to match.
- **Prevention rule:** Every state guard in an action method must be derived directly from the OMB state machine table, not inferred. Before writing `if record.state in (...)`, open the OMB section for that model and copy the allowed transition list exactly.

### LESSON-007: `statusbar_visible` only listed 3 of 5 states
- **Date:** 2026-03-02
- **Task:** TASK-P1-007 (PR review)
- **Symptom:** `statusbar_visible="open,triaged,resolved"` omitted `retry_scheduled` and `closed_with_exception`, making them invisible in the UI statusbar.
- **Root cause:** Agent listed "happy path" states; intermediate and terminal edge-case states were skipped.
- **Fix:** Set `statusbar_visible` to all 5 states from the OMB state machine.
- **Prevention rule:** `statusbar_visible` MUST list ALL states defined in the OMB state machine for that model. Copy the state list from OMB, do not filter it.

### LESSON-006: Missing `# SECURITY:` comments on `write()`/`unlink()` overrides for immutable models
- **Date:** 2026-03-02
- **Task:** TASK-P1-007 (PR review)
- **Symptom:** Immutable model overrides for `workflow.audit.event` lacked `# SECURITY:` comments explaining WHY write/unlink are blocked — violating AGENTS.md §6 comment policy.
- **Root cause:** Agent implemented the guard logic correctly but forgot to annotate it per the comment policy.
- **Fix:** Added `# SECURITY:` block comments above each override explaining the rationale and cross-referencing ACL behavior.
- **Prevention rule:** Whenever you write a `write()` or `unlink()` override that blocks an operation for security reasons, add a `# SECURITY:` block comment explaining: (a) what is blocked, (b) why, (c) how this interacts with ACLs.

---

<!-- Append new lessons above this line -->
