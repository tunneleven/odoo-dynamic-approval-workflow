# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Read first (authoritative sources)

- `AGENTS.md` is the canonical instruction file for this repo. If anything conflicts, follow `AGENTS.md`.
- At task start, read `docs/plans/2026-03-02-agent-task-execution-workflow.md` and use it as the default execution checklist.
- Read `LESSONS.md` before implementing changes.
- Architecture and requirements are defined in:
  - `dynamic_approval_workflow/docs/srs/baseline/dynamic_approval_workflow_srs_v1.3.md`
  - `dynamic_approval_workflow/docs/design/sds_dynamic_approval_workflow.md`
  - `dynamic_approval_workflow/docs/design/adr/ADR-001-three-module-architecture.md`
  - `dynamic_approval_workflow/docs/design/adr/ADR-002-full-patch-method-enforcement.md`
  - `dynamic_approval_workflow/docs/design/adr/ADR-003-bpmn-owl-lazy-loading.md`
  - `dynamic_approval_workflow/docs/design/adr/ADR-004-runtime-hybrid-scheduler.md`
  - `dynamic_approval_workflow/docs/design/adr/ADR-005-idempotency-registry.md`
  - `dynamic_approval_workflow/docs/design/omb/OMB-00-index.md` (OMB entrypoint for field/model/view/security contracts)
  - `dynamic_approval_workflow/docs/design/itm_dynamic_approval_workflow.md` (task/dependency order)

## Big-picture repository structure

- `dynamic_approval_workflow/` — Odoo addon workspace (main product code)
  - `dynamic_approval_core/` — business models, gate enforcement, runtime engine, security, callbacks, audit/idempotency
  - `dynamic_approval_bpmn/` — BPMN OWL UI + bpmn-js assets/validation (depends on `core` + `web`)
  - `dynamic_approval_operations/` — operations dashboards, retention, archival/purge (depends on `core`)
  - `.pre-commit-config.yaml` — OCA/pylint-odoo/ruff/prettier hooks
- `scripts/check_odoo19_compat.py` — repo compatibility guard for Odoo 19 XML patterns
- `.github/workflows/` — CI/policy automation (Odoo 19 compat guard, PR metadata guard, IssueOps status sync, agent auto-pick, terraform validate)
- `terraform/` — GitHub repository provisioning/governance IaC

## Architecture constraints to preserve

- Keep the 3-addon split from ADR-001; do not introduce new addons.
- `dynamic_approval_core` must not depend on `bpmn` or `operations`; `bpmn` and `operations` both depend on `core` only (plus `web` for `bpmn`).
- ORM enforcement for `orm_enforced` and `hybrid` bindings is `_patch_method`-based and fail-closed (ADR-002).
- Runtime execution is synchronous transactional tick + hybrid scheduling (`ir.cron` discovery + `queue_job` async execution) (ADR-004).
- Idempotency uses dedicated `workflow.idempotency.registry` with unique `operation_scope_hash` (ADR-005).
- BPMN integration is OWL-based lazy loading of bpmn-js assets in `dynamic_approval_bpmn` (ADR-003).

## Odoo 19 compatibility rules (high-impact)

- `res.groups` must use `privilege_id` (not `category_id`).
- `ir.cron` must not use `numbercall` or `doall`.
- Do not use `<group expand="...">` inside `<search>` views.
- Use `models.Constraint(...)` instead of `_sql_constraints`.
- `statusbar_visible` must include all states from OMB state machines.

## Non-negotiable safety constraints

- No raw SQL unless explicitly justified with `# DIRECT_SQL: <justification>`.
- No manual transaction commits (`cr.commit()`).
- No `sudo()` without documented justification.
- No client-side bypass flags for gate enforcement.
- `workflow.signature.evidence` and `workflow.audit.event` are immutable; `write()`/`unlink()` must remain blocked.

## Common commands

### Run from repository root

- Odoo 19 XML compatibility guard:
  - `python scripts/check_odoo19_compat.py --root dynamic_approval_workflow`
- Python syntax check for changed files:
  - `python -m py_compile <changed_python_files>`
- Terraform validation:
  - `terraform -chdir=terraform/foundation init -backend=false && terraform -chdir=terraform/foundation validate`
  - `terraform -chdir=terraform/governance init -backend=false && terraform -chdir=terraform/governance validate`

### Run from addon workspace

```bash
cd dynamic_approval_workflow
```

- Install pre-commit hooks:
  - `pre-commit install`
- Lint Python addons:
  - `ruff check dynamic_approval_core dynamic_approval_bpmn dynamic_approval_operations`
- Run full repo hooks:
  - `pre-commit run --all-files`
- Install one addon into a DB:
  - `odoo-bin -d <db> -i dynamic_approval_core --stop-after-init`
  - `odoo-bin -d <db> -i dynamic_approval_bpmn --stop-after-init`
  - `odoo-bin -d <db> -i dynamic_approval_operations --stop-after-init`
- Run addon test suite:
  - `odoo-bin -d <db> --test-tags /dynamic_approval_core`
  - `odoo-bin -d <db> --test-tags /dynamic_approval_bpmn`
  - `odoo-bin -d <db> --test-tags /dynamic_approval_operations`
- Run a single test method (targeted tag selector):
  - `odoo-bin -d <db> --test-tags /dynamic_approval_core:TestWorkflowDefinition.test_create_definition`
- JS lint when frontend files change:
  - `pre-commit run --all-files` (runs prettier for css/xml via repo config)
  - `eslint dynamic_approval_bpmn/static/src/` (only if ESLint is available in your local Odoo/frontend toolchain)

## PR/IssueOps constraints from repo automation

- Before creating any PR, run a Codex review on the branch diff and resolve CRITICAL/HIGH findings (or document accepted-risk rationale in the PR body).
- PR body must include both:
  - a `TASK-P...` identifier
  - the exact closing keyword line for the task issue, such as `Closes #123`
- Expected verification evidence in PRs includes:
  - `py_compile`, module install, module tests, `ruff`, `pre-commit`.
