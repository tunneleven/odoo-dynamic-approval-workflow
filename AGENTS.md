# AGENTS.md — Dynamic Approval Workflow

> Canonical instruction file for AI coding agents (OpenAI Codex, GitHub Copilot, Claude).
> Synced with `.github/copilot-instructions.md`. If they conflict, this file wins.
> Last updated: 2026-03-02

---

## 1. Project Identity

- **Project:** Dynamic Approval Workflow for Odoo 19
- **Repository layout:** 3-addon suite following OCA conventions
- **Addons:** `dynamic_approval_core`, `dynamic_approval_bpmn`, `dynamic_approval_operations`
- **Language:** Python 3.12+, JavaScript ES2022+ (OWL 2), XML, SCSS
- **Database:** PostgreSQL 15+
- **External OCA dependency:** `queue_job`

## 2. Authoritative Documents — Read Before Coding

Never invent architecture. Every decision is already documented:

| Document | Path | What it governs |
|---|---|---|
| Parent SRS | `docs/srs/baseline/dynamic_approval_workflow_srs_v1.3.md` | 95 FRs + 17 NFRs — the "what" |
| Child SRS | `docs/srs/detailed/srs_01..srs_10_*.md` | Detailed requirements per domain |
| SDS | `docs/design/sds_dynamic_approval_workflow.md` | Architecture decisions — the "how" |
| ADRs | `docs/design/adr/ADR-001..005*.md` | Key architecture decision records |
| OMB | `docs/design/omb_dynamic_approval_workflow.md` | Field-level model/view/security specs |
| ITM | `docs/design/itm_dynamic_approval_workflow.md` | Task manifest with dependency order |
| Lessons | `LESSONS.md` | Mistakes to never repeat |

**Rule:** If a document specifies a field name, type, model structure, or pattern — use it exactly. Do not rename, restructure, or "improve" documented decisions.

## 3. Module Boundaries (ADR-001)

```
dynamic_approval_core/       → All business models, runtime, enforcement, security
dynamic_approval_bpmn/       → bpmn-js OWL components, diagram assets, validation
dynamic_approval_operations/ → Dashboards, retention, archival, purge, SLO tracking
```

**Rules:**
- `core` has NO dependency on `bpmn` or `operations`.
- `bpmn` depends only on `core` (+ `web` for OWL assets).
- `operations` depends only on `core`.
- Never create cross-dependencies between `bpmn` and `operations`.
- Never create new addons without explicit ADR approval.

## 4. File Naming Conventions

### Python
- One model per file: `models/workflow_definition.py` for `workflow.definition`
- Convert dots to underscores: `workflow.node.runtime` → `workflow_node_runtime.py`
- Test files: `tests/test_<feature>.py` (e.g., `test_workflow_enforcement.py`)
- Wizard files: `wizards/workflow_<name>_wizard.py`

### XML
- Views: `views/workflow_<model>_views.xml`
- Data: `data/workflow_data.xml`, `data/ir_cron_data.xml`
- Security: `security/workflow_security.xml`, `security/ir.model.access.csv`
- Demo: `demo/workflow_demo.xml`

### JavaScript / OWL
- Components: `static/src/components/<name>/<name>.js`, `.xml`, `.scss`
- Fields: `static/src/fields/<name>.js`
- CSS prefix: `.o_daw_` (Odoo Dynamic Approval Workflow)

### Manifest
- Version format: `19.0.1.0.0` (Odoo version.major.minor.patch)
- License: `AGPL-3`
- Author must include: `Odoo Community Association (OCA)`

## 5. Python Code Standards

### Style
- PEP 8 strictly. Line length: 120 chars max (OCA standard).
- Import order: stdlib → odoo → third-party → local. Alphabetical within groups.
- Use `from odoo import api, fields, models, _` — always import `_` for translations.
- Use `from odoo.exceptions import UserError, ValidationError` — import only what you use.

### Model Definition Order
Follow this exact section order within every model file:

```python
# 1. Private attributes
_name = 'workflow.definition'
_description = 'Workflow Definition'
_inherit = ['mail.thread']
_order = 'name'

# 2. Default methods
def _default_company_id(self):
    return self.env.company

# 3. Fields (grouped: relational, then stored, then computed)
company_id = fields.Many2one(...)
name = fields.Char(...)
state = fields.Selection(...)
display_name = fields.Char(compute='_compute_display_name')

# 4. Compute methods (same order as computed fields above)
@api.depends('name')
def _compute_display_name(self):
    ...

# 5. Constraint methods
@api.constrains('name')
def _check_name(self):
    ...

# 6. Onchange methods
@api.onchange('state')
def _onchange_state(self):
    ...

# 7. CRUD overrides (create, write, unlink, copy)
@api.model_create_multi
def create(self, vals_list):
    ...

# 8. Action methods (buttons, UI actions)
def action_publish(self):
    ...

# 9. Business methods (internal logic, called by other methods)
def _evaluate_gate(self, ...):
    ...

# 10. Cron / scheduled methods
def _cron_check_sla(self):
    ...

# 11. queue_job methods
def _job_execute_callback(self, ...):
    ...
```

### Forbidden Patterns
- **Never** bypass ORM with raw SQL unless explicitly required by SDS and documented with `# DIRECT_SQL: <justification>`.
- **Never** commit transactions manually (`cr.commit()`).
- **Never** use `sudo()` without documented justification. Prefer proper access rights.
- **Never** catch bare `Exception`. Catch specific exceptions.
- **Never** use legacy `_sql_constraints`; use Odoo 19 `models.Constraint(...)` attributes.
- **Never** use mutable default arguments.
- **Never** modify `self.env.context` directly; use `self.with_context()`.
- **Never** hardcode record IDs. Use XML IDs via `self.env.ref()`.
- **Never** use Python `filtered()` for existence checks in `unlink()`/`write()` guards — use `search_count()` with `self.ids` for a single DB query (LESSON-011).
- **Never** accept optional method params (`note=None`) in `action_*` button handlers — data must come from stored fields; button methods take zero params unless OMB specifies otherwise (LESSON-009).

### Required Patterns
- All workflow models: `company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, index=True)`.
- `self.ensure_one()` at the start of single-record methods.
- `for record in self:` for multi-record iteration.
- Translatable user-facing strings: `_("Message text")`.
- Exceptions inherit from `WorkflowError` (project base exception), not raw `UserError`.
- When a model name pattern embeds the DB ID (e.g., `INC-{id}`), override `create()` to assign the name after `super().create()` — computed fields cannot reliably access `id` at compute time (LESSON-010).
- State transition guards in `action_*` methods MUST be derived from the OMB state machine table, not inferred. Copy the allowed-state list from OMB exactly (LESSON-008).

### Enforcement Interceptor (ADR-002)
- All `orm_enforced` / `hybrid` bindings use `cls._patch_method()` to wrap target business methods at registry load time.
- Wrapper checks bypass token → resolves binding → evaluates gate → audits → calls original or raises `WorkflowGateBlockedError`.
- Covers all channels: Form, RPC, import, server actions, cron, `sudo()`. Does NOT cover direct SQL.
- On interceptor error: **fail-closed** (block the action).
- Bypass only via server-side `_workflow_bypass_token` in context, set by engine internals. Every bypass is audit-logged.

## 6. Comment Policy

### Do
- Docstrings on every public method: one-line summary, then params if non-obvious.
- `# TODO(TASK-XXX):` for known incomplete work tied to ITM tasks.
- `# SECURITY:` prefix for security-critical decisions.
- `# PERF:` prefix for performance-critical decisions.
- `# ADR-XXX:` reference when implementing an architecture decision.
- `# SECURITY:` block comment required above EVERY `write()`/`unlink()` override that blocks modification for immutability — explain what is blocked, why, and how it interacts with ACLs (LESSON-006).

### Do Not
- No restating what the code does: `# Set name to value` before `self.name = value`.
- No commented-out code. Delete it; git has history.
- No author/date stamps in comments. Git blame exists.
- No ASCII art, decorative separators, or section banners in code.
- No `# pragma: no cover` without documented justification.

### Docstring Format
```python
def _evaluate_gate(self, target_model, target_method, res_ids):
    """Evaluate workflow gate for the given target operation.

    Returns gate state: 'blocked', 'allowed', or 'allowed_with_warning'.
    Raises WorkflowGateBlockedError if gate is blocked in orm_enforced mode.
    """
```

## 7. XML Standards

- 4-space indentation (OCA standard).
- Odoo 19 security model rule: `res.groups` MUST use `privilege_id`; never use `category_id` on `res.groups`.
- Group categorization must be modeled as: `ir.module.category` → `res.groups.privilege` → `res.groups`.
- Odoo 19 cron rule: never use `numbercall` or `doall` on `ir.cron` records.
- Odoo 19 search view rule: never use `<group expand="...">` inside `<search>`; use filters/separators.
- `statusbar_visible` MUST list ALL states from the OMB state machine — never a subset; copy the state list from OMB verbatim (LESSON-007).
- XML IDs: `<module_name>.<object_type>_<model_name>[_<qualifier>]`.
  - View: `dynamic_approval_core.view_workflow_definition_form`
  - Action: `dynamic_approval_core.action_workflow_definition`
  - Menu: `dynamic_approval_core.menu_workflow_root`
  - Group: `dynamic_approval_core.group_workflow_designer`
  - Rule: `dynamic_approval_core.rule_workflow_instance_company`
- `noupdate="1"` for security groups, record rules, and data that users may customize.
- `noupdate="0"` for views (so module updates apply).

## 8. JavaScript / OWL Standards

- ES2022+ syntax. Use `class` components extending `Component`.
- Template file matches component file: `bpmn_modeler.js` → `bpmn_modeler.xml`.
- Use Odoo's `rpc` service for server calls, not raw `fetch`.
- All user-facing strings through `_t()` for translation.
- No `console.log` in production code. Use Odoo's `browser.console.warn` for development only.
- CSS class prefix: `.o_daw_` to avoid collisions.

## 9. Testing Standards

### Structure
- Test files in `tests/` directory, imported via `tests/__init__.py`.
- Test class inherits `TransactionCase` (isolated) or `HttpCase` (for UI/tour tests).
- Class name: `TestWorkflow<Feature>` (e.g., `TestWorkflowEnforcement`).
- Method name: `test_<scenario>_<expected_outcome>` (e.g., `test_gate_blocked_raises_error`).

### Required Tags
```python
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestWorkflowRuntime(TransactionCase):
    ...
```

### Coverage Requirements
- Every model must have at least one test verifying create + basic constraints.
- Every business method must have positive and negative test cases.
- Every security rule must have a test verifying access granted AND denied.
- Enforcement interceptor must be tested across channels: UI, RPC, and sudo.

### Test Quality Rules
- No dynamic dates. Use `freezegun` for time-dependent tests.
- No external network calls. Mock with `patch`.
- No shared mutable state between test methods.
- Use `self.env['ir.config_parameter'].set_param()` for config, not hardcoded values.
- Assertions must have descriptive messages: `self.assertEqual(state, 'blocked', "Gate should block non-approved action")`.

## 10. Quality Gate — Mandatory Verification Stack

Run in this order after every change. All must pass before commit:

```bash
# 1. Syntax check
python -m py_compile <changed_python_files>

# 2. Module install (catches manifest, import, and data errors)
odoo-bin -d test_db -i <module_name> --stop-after-init

# 3. Test suite (catches logic errors)
odoo-bin -d test_db --test-tags /<module_name>

# 4. Python lint
ruff check <module_path>

# 5. JS lint (if JS files changed)
eslint <module_path>/static/src/

# 6. OCA pre-commit hooks
pre-commit run --all-files
```

**Failure policy:** If any step fails, fix before proceeding. Do not skip steps. Do not add `# noqa` or `# type: ignore` without documented justification.

## 11. Security Enforcement Rules

- Every model gets `ir.model.access.csv` entries for all 4 security groups.
- Every model with `company_id` gets an `ir.rule` with domain: `['|', ('company_id', '=', False), ('company_id', 'in', company_ids)]`.
- `compliance_critical` bindings cannot use `ui_only` enforcement mode.
- No client-side bypass flags for gate enforcement (SDS §7.5).
- Evidence records (`workflow.signature.evidence`) are immutable — `write()` and `unlink()` overrides block modification.
- Access grants are time-limited and audit-logged.

## 12. Git Commit Convention

Format: `[TAG] module_name: short summary`

```
[ADD] dynamic_approval_core: workflow definition model and views
[FIX] dynamic_approval_core: gate evaluation on sudo() calls
[REF] dynamic_approval_core: extract token management to helper
[IMP] dynamic_approval_bpmn: lazy-load bpmn-js assets
[TST] dynamic_approval_core: enforcement channel coverage tests
[DOC] dynamic_approval_core: add docstrings to runtime engine
```

Tags: `[ADD]` new feature, `[FIX]` bugfix, `[REF]` refactoring, `[IMP]` improvement, `[TST]` test-only, `[DOC]` documentation, `[MIG]` migration, `[REM]` removal.

**Rules:**
- One commit per logical change. Do not mix model + view + test in one commit.
- Commit message references `TASK-XXX` when implementing ITM tasks.
- Never include generated files, `__pycache__`, `.pyc`, or IDE configs.

## 13. Traceability Requirements

Every source file must be traceable to the document chain:

```
FR/NFR → DFR → SDS Section → OMB Spec → ITM TASK → Source File → Test Case
```

**In practice:**
- Model file headers do NOT need traceability comments (the OMB provides this mapping).
- Test methods SHOULD reference the requirement: `# Validates FR-008: gate enforcement on action_confirm`.
- PR descriptions MUST include: `TASK-XXX`, affected `FR/NFR` IDs, and verification evidence.
- Before creating any PR, ALWAYS run a Codex code review on the branch diff and resolve critical/high findings (or document explicit rationale for accepted risk in the PR body).

## 14. Failure Recovery Protocol

If a task fails 2 cycles in a row:

1. **Stop.** Do not retry with the same prompt.
2. Freeze the failing diff and prompt.
3. Classify root cause: unclear requirement | missing context | design conflict | tooling gap.
4. Fix the authoritative source first (SDS/OMB/ITM or this instruction file).
5. Re-run with narrower scope.
6. On third failure: escalate to human-only implementation.

## 15. Learn From Mistakes

Before starting any task, read `LESSONS.md` at the repository root.

After encountering a mistake that required > 1 fix attempt, append to `LESSONS.md`:

```markdown
### LESSON-XXX: Short title
- **Date:** YYYY-MM-DD
- **Task:** TASK-XXX
- **Symptom:** What went wrong
- **Root cause:** Why
- **Fix:** What was changed
- **Prevention:** Rule to prevent recurrence
```

## 16. Scope Boundaries — What Agents Must NOT Do

- Do not create new addons beyond the 3 in ADR-001.
- Do not add Python dependencies without explicit approval in SDS.
- Do not modify Odoo core source code (odoo/ directory).
- Do not modify openeducat_erp source code.
- Do not create database migration files unless implementing a versioned schema change.
- Do not write to files outside the `dynamic_approval_workflow/` directory tree.
- Do not invent new `FR-*`, `NFR-*`, or `DFR-*` requirement IDs.
- Do not change documented field names, model names, or API contracts from OMB.
- Do not use `ir.config_parameter` keys without `daw.` prefix (namespace isolation).

## 17. Environment Setup

```bash
# Python environment
python3 -m venv venv && source venv/bin/activate
pip install -r odoo/requirements.txt
pip install ruff pre-commit pylint-odoo

# Pre-commit hooks
cd dynamic_approval_workflow && pre-commit install

# Database
createdb daw_test
odoo-bin -d daw_test -i base,mail,queue_job --stop-after-init

# Run tests
odoo-bin -d daw_test --test-tags /dynamic_approval_core
```

## 18. Config Parameter Namespace

All system parameters use `daw.` prefix:

| Key | Type | Default | Purpose |
|---|---|---|---|
| `daw.lock_timeout_ms` | Integer | `10000` | Per-instance advisory lock timeout |
| `daw.lock_retry_count` | Integer | `3` | Lock acquisition retries |
| `daw.lock_backoff_base_ms` | Integer | `100` | Lock backoff base |
| `daw.grant_default_ttl_hours` | Integer | `24` | Access grant default TTL |
| `daw.idempotency_ttl_days` | Integer | `90` | Idempotency registry retention (OI-23 interim) |
| `daw.viewer_poll_interval_ms` | Integer | `5000` | BPMN viewer overlay poll interval |
| `daw.interceptor_cache_ttl_s` | Integer | `60` | Binding lookup cache TTL |
