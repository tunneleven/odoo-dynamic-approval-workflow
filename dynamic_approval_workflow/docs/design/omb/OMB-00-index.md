# Odoo Module Blueprint (OMB) — Dynamic Approval Workflow

Version: `v1.0`
Date: `2026-03-01`
Author: `Tech Lead`
Status: `draft`
SDS Source: `docs/design/sds_dynamic_approval_workflow.md`
SRS Baseline: `docs/srs/baseline/dynamic_approval_workflow_srs_v1.3.md`

---

## 1. Purpose

Field-level specification that AI agents can directly translate to Python models,
XML views, security CSV, OWL components, and data files. **Zero ambiguity** — every
field name, type, constraint, and default is explicitly stated. This is the primary
input document for both Copilot and Codex.

## 2. Document Structure

| Document | Scope | Path |
|---|---|---|
| **OMB-00** (this file) | Index, conventions, dependency graph | `OMB-00-index.md` |
| **OMB-01** | `dynamic_approval_core` — all 28 model specifications | `OMB-01-core-models.md` |
| **OMB-02** | `dynamic_approval_core` — view and menu specifications | `OMB-02-core-views.md` |
| **OMB-03** | `dynamic_approval_core` — security groups, ACL, record rules | `OMB-03-core-security.md` |
| **OMB-04** | `dynamic_approval_core` — cron jobs, mail templates, data, demo | `OMB-04-core-data.md` |
| **OMB-05** | `dynamic_approval_bpmn` — models, OWL components, views, security | `OMB-05-bpmn.md` |
| **OMB-06** | `dynamic_approval_operations` — models, wizards, views, security, cron | `OMB-06-operations.md` |
| **OMB-07** | Cross-module ERD, DFR-to-field traceability matrix | `OMB-07-erd-traceability.md` |

## 3. Conventions

### 3.1 Field Table Format

Every model specification uses this table format:

| Field Name | Type | Required | Default | Index | Readonly | String | Help | Constraint Notes |
|---|---|---|---|---|---|---|---|---|

- **Type**: Odoo field class with size/comodel where applicable, e.g. `Char(64)`, `Many2one('res.company')`.
- **Required**: `Yes` / `No` / `Cond` (conditional — condition stated in Constraint Notes).
- **Index**: `Yes` / `btree_not_null` / `—` / `UNIQUE(...)`.
- **Readonly**: `Yes` / `After publish` / `—`.

### 3.2 Naming Conventions

- Model names: `workflow.<domain>` (dot-separated, lowercase).
- Field names: `snake_case`, max 63 chars.
- XML IDs: `<module_short>_<object_type>_<name>`, e.g. `core_view_definition_form`.
- Selection keys: `snake_case`, no spaces.
- Timestamps: suffix `_utc` for UTC-stored datetime fields.
- Hash fields: suffix `_hash`, always `Char(64)` for SHA-256.

### 3.3 Standard Patterns

All models in `dynamic_approval_core` follow these patterns unless stated otherwise:

1. **Multi-company**: `company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company, index=True)` — or `related=` from parent.
2. **Audit timestamps**: `created_at_utc` / `occurred_at_utc` with `default=fields.Datetime.now, readonly=True`.
3. **Immutable records**: override `write()` to block immutable field updates; override `unlink()` to raise `UserError`.
4. **Correlation**: `correlation_id = fields.Char(size=64, index=True)` on event/log models.

### 3.4 SDS Binding Constraints (from SDS §19)

1. Three-module split is **final** — no further splitting or collapsing.
2. Each model/view/security artifact belongs to exactly one addon.
3. `queue_job` is a dependency of `dynamic_approval_core`.
4. Idempotency is a dedicated registry model, not ad-hoc fields.
5. Multi-company domains on all runtime objects.
6. OCA-template compliance for manifests, readme, tests.

## 4. Module Dependency Graph

```
base ──────► dynamic_approval_core ◄── mail
queue_job ─►                        ◄── web (implicit)
             │                │
             ▼                ▼
  dynamic_approval_bpmn   dynamic_approval_operations
  (depends: core, web)    (depends: core)
```

## 5. Model Dependency Graph (Core)

```
workflow.definition
  └─► workflow.definition.version
       ├─► workflow.definition.compiled
       ├─► workflow.approver.resolution
       ├─► workflow.condition.rule
       ├─► workflow.follower.rule
       └─► workflow.attestation.policy
  └─► workflow.binding
       └─► workflow.binding.scope

workflow.binding
  └─► workflow.instance
       ├─► workflow.node.runtime
       ├─► workflow.token
       ├─► workflow.decision.event
       ├─► workflow.task
       │    ├─► workflow.task.transition
       │    ├─► workflow.signature.evidence
       │    └─► workflow.access.grant
       │         └─► workflow.access.grant.log
       ├─► workflow.notification.log
       ├─► workflow.outbound.event
       ├─► workflow.incident
       └─► workflow.audit.event

workflow.delegation.record          (standalone, company-scoped)
workflow.notification.template      (standalone, company-scoped)
workflow.webhook.endpoint           (standalone, company-scoped)
workflow.idempotency.registry       (standalone, company-scoped)
workflow.definition.tag             (standalone)
workflow.approval.mixin             (abstract, no table)
workflow.enforcement.interceptor    (abstract, no table)
```

## 6. Reading Guide for AI Agents

1. Open the relevant OMB document for the module you are implementing.
2. Find the model by `_name`.
3. Copy the field table exactly — field names, types, defaults, constraints.
4. Implement SQL constraints with Odoo 19 `models.Constraint(...)` attributes from the Constraint Notes column.
5. Implement `@api.constrains` and method stubs from the Methods section.
6. Cross-reference DFR IDs to verify completeness.
7. After implementation, run verification:
   ```
   python -m py_compile <file>
   odoo-bin -d test_db -i dynamic_approval_core --stop-after-init
   ```

## 7. Sign-off

| Role | Name | Date | Approval |
|---|---|---|---|
| Tech Lead | | | |
| Product Owner | | | |
| QA Lead | | | |
