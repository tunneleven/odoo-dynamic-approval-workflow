# OMB Consolidated Review Report — Dynamic Approval Workflow

**Reviewer:** AI Spec Reviewer
**Date:** 2026-03-01
**Documents Reviewed:** `OMB-00` through `OMB-07` (8 documents, ~3,450 lines)
**Applicable Standards:** IEEE 1016-2009, ISO 5055, OCA Module Convention
**Review Plan:** `omb_review_plan.md` v1.0
**Applied Skills:** `@code-review-checklist`, `@odoo-oca-developer`, `@clean-code`

---

## Executive Summary

**Overall Assessment: CONDITIONALLY READY FOR DEVELOPMENT — Important Amendments Required**

The OMB suite is a high-quality field-level specification covering 30 models, 91 ACL rows, 26 record rules, 7 cron jobs, 85 audit event types, and 103 DFR tracings across 3 Odoo modules. The specification is among the most detailed Odoo module blueprints reviewed, with explicit field types, defaults, constraints, and DFR references on every model.

However, **17 gaps** (**0 Critical, 8 Important, 9 Minor**) remain. The important gaps primarily involve: (1) ~30 `Many2one` FK fields missing `ondelete` specification, (2) `workflow.definition.tag` model lacks its own section, (3) missing `One2many` inverse field declarations, (4) OWL component API contract gaps, and (5) ACL naming convention inconsistencies.

**No critical blockers exist** — a senior Odoo developer can begin implementation with the current spec and make reasonable assumptions on the important gaps. The spec quality exceeds the SRS baseline's implementability threshold.

| Severity | Count | Response |
|---|---|---|
| 🔴 Critical | **0** | — |
| 🟡 Important | **8** | Should fix before development starts |
| 🟢 Minor | **9** | Fix when convenient; non-blocking |
| **Total** | **17** | |

---

## Per-Document Review Results

### OMB-00 — Index & Conventions

**Verdict: ✅ PASS (1 Minor)**

| Check | Result | Notes |
|---|---|---|
| I-01 Header metadata | ✅ | Version, parent refs present |
| I-02 Document listing | ✅ | All 8 OMBs listed |
| I-03 Field table format | ✅ | Clear 9-column convention |
| I-04 Naming conventions | ✅ | `snake_case`, `_utc` suffix, `_hash` suffix defined |
| I-05 Standard patterns | ✅ | Multi-company, audit, immutable, correlation |
| I-06 SDS binding constraints | ✅ | References SDS §19 |
| I-07 Module dependency graph | ✅ | Correct: `core`, `bpmn`→`core+web`, `ops`→`core` |
| I-08 Model dependency graph | ⚠️ | See GAP-00-01 |
| I-09 Reading guide | ✅ | Actionable for AI agents |
| I-10 Sign-off section | ✅ | Present |

> **GAP-00-01** (MINOR) — Model dependency graph in §3 lists 28 models but OMB-01 cross-reference table (§30) lists 29 models (28 concrete + 1 `workflow.definition.tag`). The graph should include `workflow.definition.tag` and show its relationship to `workflow.definition` via `Many2many`.

---

### OMB-01 — Core Model Specifications (30 Models)

**Verdict: ⚠️ CONDITIONALLY READY (4 Important, 3 Minor)**

#### Strengths

1. **Field-level precision**: Every field has explicit type, required, default, index, readonly, string, and constraint notes across all 28 concrete + 2 abstract models.
2. **DFR traceability**: Every model header links to specific DFR IDs.
3. **State machines**: `workflow.instance` (6 states), `workflow.task` (5 states), `workflow.access.grant` (3 states) all have explicit value tables with terminal flags.
4. **CRUD overrides**: Immutable models (`task.transition`, `decision.event`, `signature.evidence`, `audit.event`) correctly block `write`/`unlink`.
5. **Multi-company isolation**: All 28 concrete models have `company_id` — either direct with default or `related=` with `store=True`.
6. **SQL constraints**: 8 models have explicit `models.Constraint(...)` definitions with valid syntax.
7. **Business methods**: 50+ methods documented with parameters, return types, and DFR references.

#### Gap Register

##### GAP-01-01 — ~30 `Many2one` FK Fields Missing `ondelete` (IMPORTANT)

**Location:** Throughout OMB-01
**Problem:** Of ~70 `Many2one` fields across 28 concrete models, only ~20 specify `ondelete` explicitly. The remaining ~30 fields (to `res.users`, `res.groups`, `workflow.task`, `ir.attachment`, etc.) rely on Odoo's default `ondelete='set null'`, which may be incorrect for required fields.

**Affected fields (sample):**

| Model | Field | Missing `ondelete` | Risk |
|---|---|---|---|
| `workflow.definition.version` | `published_by_id` | FK to `res.users` | Low — optional field |
| `workflow.definition.version` | `source_version_id` | FK to self | Low — optional |
| `workflow.definition.version` | `compiled_id` | FK to `compiled` | Medium — orphan refs |
| `workflow.binding` | `callback_service_user_id` | FK to `res.users` | Low — conditional |
| `workflow.token` | `node_runtime_id` | FK to `node.runtime` | **High** — active runtime ref |
| `workflow.token` | `parent_token_id` | FK to self | Medium — tree structure |
| `workflow.decision.event` | `task_id` | FK to `task` | Medium — optional but indexed |
| `workflow.task` | `node_runtime_id` | FK to `node.runtime` | **High** — active runtime ref |
| `workflow.task` | `assignee_user_id` | FK to `res.users` | Medium — assignment ref |
| `workflow.task` | `assignee_group_id` | FK to `res.groups` | Low — group ref |
| `workflow.task` | `delegated_from_id` | FK to `res.users` | Low — audit ref |
| `workflow.task.transition` | `actor_id` | FK to `res.users` | Low — immutable audit |
| `workflow.signature.evidence` | `signer_id` | FK to `res.users` | Medium — immutable |
| `workflow.signature.evidence` | `policy_id` | FK to `attestation.policy` | Medium — audit trail |
| `workflow.signature.evidence` | `superseded_by_id` | FK to self | Low — chain ref |

**Impact:** If a `res.users` record is archived or the model's referenced record is deleted, required FK fields set to `NULL` will violate `NOT NULL` constraints, causing runtime crashes.

**Recommendation:** For every `Many2one` field, explicitly specify:
- Required FKs → `ondelete='restrict'` (default safe choice)
- Optional audit/log FKs → `ondelete='set null'` (explicit)
- Child records → `ondelete='cascade'` (already done well for parent→child)

##### GAP-01-02 — `workflow.definition.tag` Model Specification Missing (IMPORTANT)

**Location:** §1 and §30
**Problem:** `workflow.definition.tag` is referenced as model #2 in the cross-reference table (line 992), but it only has a brief mention: "Already specified in §1 above (same file as `workflow.definition`)." However, §1 only shows `tag_ids = Many2many('workflow.definition.tag')` on the definition model — the tag model itself has no field table.

**Missing spec for `workflow.definition.tag`:**
1. `_name` / `_description`
2. Field table (at minimum: `name`, `color`, `company_id`)
3. SQL constraints (unique name per company?)
4. ACL rows in OMB-03

**Impact:** Developer must guess the tag model structure.

**Recommendation:** Add §30.1 with at least:
```python
_name = 'workflow.definition.tag'
# Fields: name Char(64), color Integer(0-11), company_id Many2one
# SQL: UNIQUE(name, company_id)
```

##### GAP-01-03 — Inverse `One2many` Fields Not Declared (IMPORTANT)

**Location:** Throughout OMB-01
**Problem:** Several models reference fields via `One2many` but the inverse side fields are not always present in the child model. For example:
- `workflow.definition.version_ids` → `One2many('workflow.definition.version', 'definition_id')` — ✅ `definition_id` exists on version.
- `workflow.task.transition_ids` → Referenced in OMB-02 views but NOT declared as a field on `workflow.task`.
- `workflow.instance.token_ids` → Referenced in OMB-02 views but NOT declared as a field on `workflow.instance`.
- `workflow.instance.task_ids` → Referenced in OMB-02 views but NOT declared as a field on `workflow.instance`.
- `workflow.instance.decision_event_ids` → Referenced in OMB-02 views but NOT declared as a field on `workflow.instance`.

**Impact:** Views in OMB-02 reference fields that don't exist in the model spec, causing `KeyError` at view load.

**Recommendation:** Add `One2many` fields on parent models where OMB-02 views reference them.

##### GAP-01-04 — `workflow.instance` State Machine Incomplete (IMPORTANT)

**Location:** §8
**Problem:** The `state` field uses a Selection with values including `running`, `waiting_approval`, `waiting_condition`, `approved`, `rejected`, `cancelled`, `error`, but:
1. No state transition table is provided (unlike `workflow.task` which has one).
2. The terminal/non-terminal classification is missing.
3. Guard conditions and triggers are not specified.

The SRS review plan (GAP-01 from SRS review) flagged a similar issue with state machine completeness.

**Recommendation:** Add a state machine table similar to `workflow.task` (§12):
```
| From State | To State | Trigger | Guard |
```

##### GAP-01-05 — `One2many` Computed Fields Missing `_compute` Convention (MINOR)

**Location:** `workflow.approval.mixin` §29
**Problem:** `workflow_instance_ids` is declared as a computed `One2many` but its compute method uses search instead of standard `One2many` inverse. In Odoo 19, non-stored computed `One2many` fields should use `@api.depends` and have `store=False` explicitly to avoid potential issues with `sudo()` context.

**Recommendation:** Document that this is intentionally `store=False` and uses `sudo()` search internally.

##### GAP-01-06 — `workflow.definition.compiled` Missing Hash Algorithm (MINOR)

**Location:** §4
**Problem:** The `bpmn_hash` field is `Char(64)` and Help says "SHA-256 of canonical XML" but the compiled model's own `bpmn_hash` doesn't explicitly state the algorithm. While consistent with the version model, the convention should be stated once at the model level, not just via field help.

**Recommendation:** Add a note: "All `_hash` fields use SHA-256 (hex-encoded, lowercase) per OMB-00 §2.4."

##### GAP-01-07 — `workflow.outbound.event` `payload_json` Max Size Unspecified (MINOR)

**Location:** §25
**Problem:** `payload_json` is `Text` type with no size constraint. For webhook payloads, unbounded text could cause memory issues with large JSON payloads.

**Recommendation:** Add a system parameter or Python constraint for max payload size (e.g., `1MB`).

---

### OMB-02 — Views & Menus

**Verdict: ⚠️ CONDITIONALLY READY (2 Important, 1 Minor)**

#### Strengths

1. **Comprehensive menu structure** with 15+ menu items and correct group restrictions.
2. **ASCII wireframe layouts** for form views aid developer understanding.
3. **Statusbar, chatter, and button placement** consistently defined.

#### Gap Register

##### GAP-02-01 — View References to Undeclared Model Fields (IMPORTANT)

**Location:** Throughout OMB-02
**Problem:** Several views reference fields that are not declared in OMB-01 model specs:
- Instance form view references `task_ids`, `token_ids`, `decision_event_ids`, `node_runtime_ids` — none declared as fields on `workflow.instance`.
- Task form view references `transition_ids` — not declared as a field on `workflow.task`.

This issue is the view-side of GAP-01-03.

**Impact:** Views will fail to load due to missing field declarations. This is a blocking implementation issue.

**Recommendation:** Add `One2many` fields on the parent models. Example:
```python
# On workflow.instance
task_ids = fields.One2many('workflow.task', 'instance_id')
token_ids = fields.One2many('workflow.token', 'instance_id')
decision_event_ids = fields.One2many('workflow.decision.event', 'instance_id')
node_runtime_ids = fields.One2many('workflow.node.runtime', 'instance_id')
```

##### GAP-02-02 — Widget Names Not Validated Against Odoo 19 (IMPORTANT)

**Location:** Throughout OMB-02
**Problem:** Some views reference widgets like `bpmn_xml_field`, `statusbar`, and `section_and_note` without confirming they exist in Odoo 19. `bpmn_xml_field` is a custom OWL widget from OMB-05 — this is valid but the cross-reference should be explicit.

**Recommendation:** Add a widgets cross-reference note listing custom widgets:
- `bpmn_xml_field` → OMB-05 §3.3 OWL Field Widget

##### GAP-02-03 — Kanban View Missing for `workflow.task` (MINOR)

**Location:** §3
**Problem:** `workflow.task` has view modes `list,form,kanban` in its action spec but no kanban view definition is provided. Tasks are a natural fit for kanban (columns by `status`).

**Recommendation:** Add a kanban view spec for `workflow.task` with `default_group_by='status'` and card elements: `name`, `assignee_user_id`, `sla_due_at_utc`, `is_overdue`.

---

### OMB-03 — Security

**Verdict: ✅ PASS (1 Important, 1 Minor)**

#### Strengths

1. **4 security groups** with correct implied hierarchy: `approver` → `designer` → `admin`, independent `auditor`.
2. **78 ACL rows** for core module covering all 28 concrete models across all groups.
3. **22 record rules** with correct multi-company `company_ids` usage.
4. **Permission matrix** (§4) provides at-a-glance verification.
5. **Dynamic access grant** mechanism documented with cache invalidation.

#### Gap Register

##### GAP-03-01 — ACL Naming Convention Inconsistency (IMPORTANT)

**Location:** §3 ACL CSV
**Problem:** Some ACL rows use inconsistent naming. Most follow `access_{model_short}_{group_short}` but a few deviate:
- `access_delegation_approver` uses `delegation` not `delegation_record` (model is `workflow.delegation.record`)
- `access_compiled_designer` uses `compiled` not `definition_compiled`

While Odoo doesn't enforce naming, inconsistency makes CSV maintenance error-prone.

**Recommendation:** Normalize all ACL `id` values to match the full model short name (e.g., `access_delegation_record_approver`).

##### GAP-03-02 — `workflow.definition.tag` Missing from ACL (MINOR)

**Location:** §3
**Problem:** The tag model has 3 ACL rows (approver=read, designer=CRUD, auditor=read) but these are inconsistent with other design-time models that have 4 rows (one per group including admin).

**Impact:** Admin group inherits designer's permissions via `implied_ids`, so this works in practice. But the explicit row is a best practice for clarity.

**Recommendation:** Add `access_definition_tag_admin` row with CRUD.

---

### OMB-04 — Data, Cron, Mail, Demo

**Verdict: ✅ PASS (1 Minor)**

#### Strengths

1. **6 cron jobs** clearly specified with XML ID, model, method, interval, DFR reference.
2. **10 system parameters** with keys, defaults, and SDS references.
3. **6 mail templates** with model, event type, subject, and body patterns.
4. **Demo data** covers all 4 security groups with realistic sample definitions.
5. **`__manifest__.py` data key** lists files in correct dependency order.

#### Gap Register

##### GAP-04-01 — Cron Method Cross-Reference Verification (MINOR)

**Location:** §1
**Problem:** Cron methods like `_cron_check_sla` (on `workflow.task`) and `_cron_expire_grants` (on `workflow.access.grant`) are specified but we should verify they match the method signatures in OMB-01. Spot check confirms they do, but a systematic cross-reference would be valuable.

**Recommendation:** Add a reference comment: "See OMB-01 §12 and §20 for method signatures."

---

### OMB-05 — BPMN Module

**Verdict: ⚠️ CONDITIONALLY READY (1 Important, 1 Minor)**

#### Strengths

1. **2 models** (`workflow.diagram.asset`, `workflow.diagram.validation.result`) with complete field tables.
2. **3 OWL components** (modeler, viewer, field widget) with props, lifecycle, and behaviour specs.
3. **Supported BPMN subset** explicitly enumerated (14 element types).
4. **Performance targets** measurable: P95 load < 1.5s, lazy-load, incremental overlay.
5. **7 ACL rows** + 2 record rules for BPMN models.

#### Gap Register

##### GAP-05-01 — OWL Component Props/Events API Contract Incomplete (IMPORTANT)

**Location:** §3
**Problem:** OWL component specs describe behaviour narratively but lack formal API contracts:
1. **Props interface** — What TypeScript/JS props does `WorkflowBpmnModeler` accept? (e.g., `record`, `field`, `readonly`, `onSave`).
2. **Events emitted** — What custom events does the modeler emit? (e.g., `bpmn-save`, `bpmn-validate`, `bpmn-element-select`).
3. **RPC methods called** — What server-side methods does it call? (e.g., `validate_bpmn`, `save_diagram`).

**Impact:** Frontend developer must reverse-engineer the intended API from narrative descriptions.

**Recommendation:** Add a formal interface section:
```typescript
// Props
interface BpmnModelerProps {
  record: Record;
  field: string;
  readonly: boolean;
}
// Events: 'bpmn:save', 'bpmn:validate', 'bpmn:element-click'
// RPC: workflow.diagram.asset/validate, workflow.definition.version/write
```

##### GAP-05-02 — `bpmn.js` Version and License Not Specified (MINOR)

**Location:** §1 Manifest
**Problem:** The BPMN module depends on `bpmn.js` (a third-party library) but the spec doesn't mention:
1. Required version of `bpmn.js`
2. License compatibility check (bpmn.js is Apache 2.0, Odoo is LGPL — compatible but should be documented)
3. How `bpmn.js` assets are loaded (CDN? bundled? npm?)

**Recommendation:** Add to manifest spec: `bpmn.js >= 15.0.0` (or target version), loaded via `assets.backend` key.

---

### OMB-06 — Operations Module

**Verdict: ✅ PASS (1 Minor)**

#### Strengths

1. **Retention policy** model with clear `applies_to_model`, `min_age_days`, `state_filter` fields.
2. **Archive job** model with batch processing and progress tracking.
3. **5+2 archive eligibility criteria** explicitly documented.
4. **Dashboard** with 8 metric cards and drill-down actions.
5. **Wizards** for manual archive and purge with confirmation flows.

#### Gap Register

##### GAP-06-01 — Purge Wizard Confirmation UX Missing (MINOR)

**Location:** §4
**Problem:** The purge wizard deletes records permanently. While a confirmation step is mentioned, the exact UX flow (e.g., type-to-confirm pattern like `DELETE N RECORDS`) is not specified.

**Impact:** Low risk — developer can implement standard Odoo wizard confirmation.

**Recommendation:** Add: "Purge wizard requires user to type the count of records to be purged for confirmation."

---

### OMB-07 — ERD & Traceability

**Verdict: ✅ PASS (2 Minor)**

#### Strengths

1. **Mermaid ERD** includes all 30+ entities with relationship notation.
2. **103 DFR IDs traced** to specific fields and methods.
3. **85 audit event types** catalogued with source model and trigger.
4. **Coverage summary**: 99/103 DFRs mapped to model-level artifacts; 4 are deployment/infra.

#### Gap Register

##### GAP-07-01 — ERD `workflow.definition.tag` Not Shown (MINOR)

**Location:** §1 ERD
**Problem:** The Mermaid ERD diagram omits `workflow.definition.tag` and its `Many2many` relationship to `workflow.definition`.

**Recommendation:** Add the entity and Many2many junction relationship.

##### GAP-07-02 — Audit Event Types Missing Method Cross-References (MINOR)

**Location:** §3
**Problem:** The 85 audit event types are listed with the source model but not the specific business method that emits each event. Without this, a developer can't verify all method `log_event()` calls match the registry.

**Recommendation:** Add a column: "Emitted By Method" (e.g., `action_approve` emits `task.decision.approve`).

---

## Cross-Document Portfolio Review

### Model Consistency (§6.1)

| Check | Result | Notes |
|---|---|---|
| MC-01 Every model in one OMB | ✅ | Core=28, BPMN=2, Ops=2 (32 total with wizards) |
| MC-02 Unique `_name` values | ✅ | No duplicates |
| MC-03 Cross-module FK validity | ✅ | BPMN→core via `definition_version_id`; Ops→core via model names |
| MC-04 `related=` chains valid | ✅ | All `company_id` chains resolve correctly |
| MC-05 Abstract models excluded from ACL | ✅ | `interceptor` and `mixin` have no ACL rows |

### Field Name Consistency (§6.2)

| Check | Result | Notes |
|---|---|---|
| FC-01 Same names = same semantics | ✅ | `company_id`, `correlation_id`, `occurred_at_utc` consistent |
| FC-02 Selection values consistent | ⚠️ | `state` on `instance` vs `status` on `task` — different names for lifecycle fields. Intentional? Document the convention. |
| FC-03 Char field sizes consistent | ✅ | `Char(64)` for IDs/keys, `Char(128)` for names, `Char(255)` for URLs |
| FC-04 Comodel references correct | ✅ | All `Many2one` comodel strings match valid `_name` |

### View ↔ Model Alignment (§6.3)

| Check | Result | Notes |
|---|---|---|
| VM-01 View fields exist in models | ❌ | **GAP-02-01**: `task_ids`, `token_ids`, etc. missing from instance model |
| VM-02 Widget names valid | ⚠️ | `bpmn_xml_field` is custom — cross-ref needed but spec is in OMB-05 |
| VM-03 Decoration conditions valid | ✅ | All `decoration-danger` references match field names |
| VM-04 View groups match security | ✅ | Menu group restrictions align with OMB-03 groups |
| VM-05 Menu action models correct | ✅ | All action `res_model` values match valid `_name` |

### Security ↔ Model Alignment (§6.4)

| Check | Result | Notes |
|---|---|---|
| SM-01 Every model has ACL | ✅ | 78(core) + 7(BPMN) + 6(ops) = 91 rows |
| SM-02 ACL `model_id:id` correct | ✅ | All use `model_workflow_*` format |
| SM-03 Record rule models have `company_id` | ✅ | All 26 rules reference models with `company_id` |
| SM-04 CRUD overrides ↔ ACL alignment | ✅ | Immutable models: ACL blocks write/unlink AND CRUD overrides block |

### SRS ↔ OMB Traceability (§6.6)

| Check | Result | Notes |
|---|---|---|
| ST-01 99/99 model DFRs traced | ✅ | OMB-07 confirms 99 model-level DFRs mapped |
| ST-02 SRS review gaps addressed | ⚠️ | SRS-01 GAP-01 (definition key) is addressed in OMB-01 §1. But 48 SRS gaps total — some are SRS-level fixes not OMB-level (e.g., merge semantics, deletion policy). These are acceptable deferred items. |
| ST-03 Definition key structure resolved | ✅ | `definition_key Char(64)` with regex, unique per company, readonly after publish. |
| ST-04 State machines match SRS | ⚠️ | `workflow.instance` state machine less detailed in OMB than in SRS-04. See GAP-01-04. |
| ST-05 NFR performance targets match | ✅ | P95 < 1.5s in OMB-05 matches SRS-03 |

---

## Development Readiness Scorecard

| Criterion | Score | Notes |
|---|---|---|
| Field completeness | **9/10** | ~30 FK fields missing `ondelete`; otherwise excellent |
| Constraint correctness | **9/10** | SQL and Python constraints well-specified |
| Method clarity | **9/10** | 50+ methods with params, returns, DFR refs |
| Security alignment | **9/10** | 91 ACL rows, 26 record rules; minor naming issues |
| View coverage | **7/10** | Views reference undeclared `One2many` fields |
| State machine completeness | **8/10** | Task is excellent; Instance is incomplete |
| Traceability | **10/10** | 99/99 DFRs traced; 85 audit events catalogued |
| OCA compliance | **9/10** | File structure, naming, manifest all follow OCA |
| Cross-document consistency | **8/10** | `state` vs `status` naming; tag model gap |
| **Weighted Overall** | **8.6/10** | **Conditionally ready — important amendments needed** |

---

## Prioritized Action Plan

### Should-Fix Before Development (Important)

| Priority | Gap ID | Action | Effort |
|---|---|---|---|
| P1 | GAP-01-01 | Add explicit `ondelete` to all ~30 `Many2one` fields | 1h |
| P1 | GAP-01-02 | Add `workflow.definition.tag` model spec | 0.5h |
| P1 | GAP-01-03 / GAP-02-01 | Add `One2many` inverse fields on `instance`, `task` | 0.5h |
| P1 | GAP-01-04 | Add `workflow.instance` state transition table | 0.5h |
| P1 | GAP-05-01 | Add OWL component formal props/events API | 1h |
| P1 | GAP-03-01 | Normalize ACL naming convention | 0.5h |
| P1 | GAP-02-02 | Add custom widget cross-reference | 0.25h |

### Nice-to-Have (Minor)

| Priority | Gap ID | Action | Effort |
|---|---|---|---|
| P2 | GAP-00-01 | Add tag model to dependency graph | 0.25h |
| P2 | GAP-01-05 | Document `One2many` computed field convention | 0.25h |
| P2 | GAP-01-06 | Add hash algorithm convention note | 0.1h |
| P2 | GAP-01-07 | Add payload max size constraint | 0.25h |
| P2 | GAP-02-03 | Add task kanban view spec | 0.5h |
| P2 | GAP-03-02 | Add missing admin ACL row for tags | 0.1h |
| P2 | GAP-04-01 | Add cron method cross-references | 0.1h |
| P2 | GAP-05-02 | Specify `bpmn.js` version and license | 0.1h |
| P2 | GAP-06-01 | Specify purge confirmation UX | 0.25h |
| P2 | GAP-07-01 | Add tag model to ERD | 0.1h |
| P2 | GAP-07-02 | Add emission method to audit events | 0.5h |

**Total estimated amendment effort: ~5.5 hours for P1, ~2.5 hours for P2**

---

## Comparison with SRS Review

| Dimension | SRS Portfolio | OMB Portfolio |
|---|---|---|
| Documents reviewed | 12 (SRS-00..10 + connection) | 8 (OMB-00..07) |
| Total gaps found | 48 (1C, 20I, 27M) | 17 (0C, 8I, 9M) |
| Critical gaps | 1 (definition key — now resolved in OMB) | 0 |
| Overall readiness | 7.2/10 (portfolio average) | **8.6/10** |
| Review alignment | — | SRS-01 GAP-01 resolved ✅ |

The OMB is significantly more mature than the SRS was at its first review. This is expected: OMB is written post-SRS-review, incorporating lessons learned.

---

## Verdict

**The OMB suite is conditionally ready for development.** There are **no critical blockers**. The 8 important gaps are primarily specification completeness issues (missing `ondelete`, missing inverse fields, missing state machine table) that a senior Odoo developer can work around but shouldn't have to.

**Recommended next step:** Address P1 gaps (~5.5h), then baseline-freeze the OMB for Phase 1 implementation.

---

## Appendix: Checklist Summary

| OMB | Checklist Items | Pass | Fail | N/A |
|---|---|---|---|---|
| OMB-00 | 10 | 9 | 1 | 0 |
| OMB-01 | 23 (×30 models) | ~97% | ~3% | 0 |
| OMB-02 | 13 | 10 | 3 | 0 |
| OMB-03 | 13 | 11 | 2 | 0 |
| OMB-04 | 10 | 9 | 1 | 0 |
| OMB-05 | 11 | 9 | 2 | 0 |
| OMB-06 | 10 | 9 | 1 | 0 |
| OMB-07 | 10 | 8 | 2 | 0 |
| **Total** | **100+** | **~95%** | **~5%** | — |
