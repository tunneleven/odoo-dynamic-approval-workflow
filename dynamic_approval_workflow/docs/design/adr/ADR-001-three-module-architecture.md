# ADR-001: Three-Module Architecture

**Status:** Accepted  
**Date:** 2026-03-01  
**Decision Makers:** Tech Lead, Product Owner  
**SDS Reference:** §3 Module Structure

---

## Context

The Dynamic Approval Workflow system has ~25 domain models spanning 10 SRS domains (definition, binding, runtime, tasks, signatures, notifications, webhooks, idempotency, incidents, operations). The system needs to be packaged as Odoo 19 addons following OCA conventions.

Three options were considered:

1. **Single module** — all models in one addon.
2. **3 modules** — core + bpmn + operations.
3. **6 modules** — core, definition, runtime, participant, integration, operations.

## Decision

**Option 2: Three modules** — `dynamic_approval_core`, `dynamic_approval_bpmn`, `dynamic_approval_operations`.

## Rationale

### Why not single module?
- The bpmn-js JavaScript library (~2MB) would be loaded for all users, even those who never touch the diagram designer.
- Operations/retention logic would be mandatory even in dev/test where it adds complexity.
- OCA review and maintenance is harder with a monolithic addon.

### Why not 6 modules?
- 6 modules create a deep dependency chain (`core → definition → runtime → participant → integration → operations`) which complicates install and testing.
- Cross-module model references multiply — e.g., `workflow.task` needs to reference `workflow.instance` and `workflow.definition.version`, which in a 6-module split live in different addons.
- AI agents (Copilot/Codex) work better with fewer context boundaries.
- Maintenance cost of 6 manifests, 6 security files, 6 test suites is disproportionate at this project scale.

### Why 3 modules works
- **`dynamic_approval_core`** is self-sufficient: it contains all business logic models and can run headless (API-driven, no diagram UI).
- **`dynamic_approval_bpmn`** isolates the heavy JS dependency so it is only loaded for designers/viewers. It can be omitted for setups that use API-only workflow definitions.
- **`dynamic_approval_operations`** isolates monitoring/dashboards/retention so QA/dev environments can skip it.
- No circular dependencies: `bpmn → core`, `operations → core`.
- Each module has a clear, testable acceptance boundary.

## Consequences

### Positive
- Simpler dependency graph (max depth: 1 hop from core).
- Each module is independently installable and testable.
- bpmn-js loaded only when `dynamic_approval_bpmn` is installed.
- OCA review scope is manageable (3 manifests, 3 security files).

### Negative
- `dynamic_approval_core` is large (~25 models). Risk of monolithic feel mitigated by strict one-model-per-file convention.
- If a future domain grows significantly (e.g., notification templates become a full CMS-like system), it may warrant extraction. Document extraction criteria: if a sub-domain exceeds 8 models AND has consumers outside core, it is a candidate.

### Module Acceptance Criteria

Each module must independently pass:

| Criterion | Command |
|---|---|
| Install | `odoo-bin -d test_db -i <module> --stop-after-init` |
| Tests | `odoo-bin -d test_db --test-tags /<module>` |
| Lint | `ruff check <module> && pre-commit run --all-files` |
| Security | All models have `ir.model.access.csv` entries |
| Manifest | OCA-compliant `19.0.x.y.z` version |
| README | `readme/DESCRIPTION.rst` present |

## Alternatives Considered

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| Single module | Simplest | JS bloat, no selective install | Rejected |
| 3 modules | Balanced | Core is large | **Accepted** |
| 6 modules | Maximum separation | Deep deps, complex AI context | Rejected |

## References

- SRS-00..SRS-10 (full portfolio)
- OCA module conventions: `readme/`, `__manifest__.py`, one-model-per-file
- Parent SRS §9 (domain model listing), §18 (mixin pattern)
