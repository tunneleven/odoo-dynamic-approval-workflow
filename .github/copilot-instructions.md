<!-- Copilot reads the first ~4000 characters for code review. Critical rules go first. -->
<!-- Synced with AGENTS.md (canonical source). If they conflict, AGENTS.md wins. -->
<!-- Last sync: 2026-03-01 -->

# Dynamic Approval Workflow — Copilot Instructions

## Identity
Odoo 19 approval workflow system. 3 addons: `dynamic_approval_core`, `dynamic_approval_bpmn`, `dynamic_approval_operations`. OCA conventions. Python 3.12+, OWL 2, PostgreSQL 15+.

## Critical Rules (Code Review Gate)

1. **Follow the docs.** Architecture is in `docs/design/sds_dynamic_approval_workflow.md`. Field specs in OMB. Do not invent.
2. **One model per file.** `workflow.node.runtime` → `models/workflow_node_runtime.py`.
3. **company_id on every model.** `fields.Many2one('res.company', required=True, default=lambda self: self.env.company, index=True)`.
4. **Security complete.** Every model has `ir.model.access.csv` + `ir.rule` for company isolation.
5. **No raw SQL** without `# DIRECT_SQL: <justification>`. No `cr.commit()`. No mutable defaults.
6. **No bare Exception.** Catch specific. Project exceptions inherit `WorkflowError`.
7. **No sudo() without justification.** Prefer proper access rights.
8. **No client-side bypass flags** for gate enforcement.
9. **Evidence is immutable.** `workflow.signature.evidence` blocks `write()` and `unlink()`.
10. **Tokens never deleted.** State transitions only: `active` → `consumed` / `cancelled`.
11. **Fail-closed.** Interceptor errors block the action in `orm_enforced` / `hybrid` modes.
12. **Read `LESSONS.md`** before starting work. Append mistakes that took > 1 fix.
13. **Odoo 19 group schema.** `res.groups` uses `privilege_id` (not `category_id`).
14. **Odoo 19 cron schema.** `ir.cron` must not use removed fields `numbercall` or `doall`.
15. **Odoo 19 search views.** Do not use `<group expand="...">` in `<search>` arches.
16. **Odoo 19 constraints.** Use `models.Constraint(...)`; do not use `_sql_constraints`.

## Comment Policy
- Docstrings on public methods: one-line summary + params if non-obvious.
- `# TODO(TASK-XXX):` for incomplete work tied to ITM.
- `# SECURITY:`, `# PERF:`, `# ADR-XXX:` prefixes for critical decisions.
- No restating code. No commented-out code. No author stamps. No ASCII art.

## Python Style
- PEP 8. Line length 120. Import order: stdlib → odoo → third-party → local.
- Model section order: private attrs → defaults → fields → compute → constraints → onchange → CRUD → actions → business → cron → queue_job.
- `self.ensure_one()` for single-record methods. `for record in self:` for multi.
- Translatable strings: `_("text")`. Config params: `daw.` prefix.

## Testing
- `TransactionCase` or `HttpCase`. Tag: `@tagged('post_install', '-at_install')`.
- Test name: `test_<scenario>_<expected>`. Assertions need messages.
- No dynamic dates (use `freezegun`). No network calls (use `patch`).
- Test both positive AND negative cases. Test security rules: access granted AND denied.

## Quality Gate (all must pass)
```bash
python -m py_compile <files>
odoo-bin -d test_db -i <module> --stop-after-init
odoo-bin -d test_db --test-tags /<module>
ruff check <module_path>
pre-commit run --all-files
```

## Module Boundaries (ADR-001)
- `core` has NO dependency on `bpmn` or `operations`.
- `bpmn` depends only on `core` + `web`.
- `operations` depends only on `core`.
- No cross-deps between `bpmn` and `operations`.
- No new addons without ADR approval.

## Architecture Decisions (SDS)
- **ADR-002:** Full `_patch_method` enforcement for all bound models at registry load.
- **ADR-003:** bpmn-js loaded lazily via OWL `onWillStart` + `loadJS()`.
- **ADR-004:** Hybrid scheduler — `ir.cron` for scanning, `queue_job` for async execution.
- **ADR-005:** Idempotency via dedicated `workflow.idempotency.registry` model with UNIQUE scope hash.

## XML
- 4-space indent. XML IDs: `<module>.<type>_<model>[_<qualifier>]`.
- For security groups in Odoo 19: `ir.module.category` → `res.groups.privilege` → `res.groups`.
- `noupdate="1"` for security data. `noupdate="0"` for views.

## JavaScript / OWL
- ES2022+. OWL 2 components extending `Component`.
- CSS prefix `.o_daw_`. Use `rpc` service, not `fetch`. Strings via `_t()`.

## Git Commits
`[TAG] module_name: short summary` — Tags: ADD, FIX, REF, IMP, TST, DOC, MIG, REM.

## Forbidden
- No modifying `odoo/` core or `openeducat_erp/`.
- No new addons, FR/NFR/DFR IDs, or field name changes from OMB.
- No `ir.config_parameter` without `daw.` prefix.
- No files outside `dynamic_approval_workflow/`.

## Failure Recovery
If a task fails 2 cycles: stop → classify root cause → fix source doc → narrow scope → retry once → escalate to human on third failure.

## Reference Documents
| Doc | Path |
|---|---|
| SDS | `docs/design/sds_dynamic_approval_workflow.md` |
| ADRs | `docs/design/adr/ADR-001..005*.md` |
| SRS | `docs/srs/baseline/dynamic_approval_workflow_srs_v1.3.md` |
| Lessons | `LESSONS.md` |
| Full rules | `AGENTS.md` |
