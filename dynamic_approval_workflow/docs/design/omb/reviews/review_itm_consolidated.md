# ITM Review Report — Consolidated Findings

Version: `v1.0` | Date: `2026-03-01` | Reviewer: `AI (project-planner + code-review-checklist)`

---

## Summary

| Severity | Count | Description |
|---|---|---|
| **P0 Critical** | 0 | — |
| **P1 High** | 3 | 3 tasks exceed max-3-files constraint |
| **P2 Medium** | 3 | 2 SDS §16 files missing; vague business logic in 11 tasks |
| **P3 Low** | 2 | Minor style/coverage items |
| **Total** | **8** | |

---

## ✅ Checks Passed

| Check | Result |
|---|---|
| All 30 OMB-01 models covered | ✅ All present |
| All OMB-02 view specs covered | ✅ 6/6 view files |
| All OMB-05 OWL components covered | ✅ Modeler + Viewer + Field widget |
| All OMB-06 ops specs covered | ✅ Retention, archive, purge, dashboard |
| Dependency ordering | ✅ No forward deps, no missing refs |
| Task field completeness | ✅ All 55/55 have all required fields |
| verification_command present | ✅ 55/55 |
| acceptance_criteria present | ✅ 55/55 |
| labels present | ✅ 55/55 |
| blueprint_sections present | ✅ 55/55 |
| Blocker tags applied | ✅ OI-15 (2 tasks), OI-23 (1 task) |
| Pre-completed tasks marked | ✅ 4 tasks |
| Unique files referenced | 76 files |

---

## P1 — High: Max-3-Files Constraint Violations

> SDS §19 rule: "Each task produces at most 3 files."

### F-001: TASK-P3-007 — 5 files
**Current:** `models/__init__.py`, `models/workflow_diagram_asset.py`, `models/workflow_diagram_validation_result.py`, `__init__.py`, `__manifest__.py`

**Fix:** Split into two tasks:
- TASK-P3-007a: `__init__.py`, `__manifest__.py`, `models/__init__.py` (scaffold)
- TASK-P3-007b: `models/workflow_diagram_asset.py`, `models/workflow_diagram_validation_result.py`  
- *Or:* since scaffold is `pre_completed`, remove `__init__.py` and `__manifest__.py` from `files_to_create` → move to `files_to_modify` (those exist). Leaves 3 create files — but `models/__init__.py` is a create. So: move `__init__.py`, `__manifest__.py` to `files_to_modify` → 1 create + 2 modify = 3 total ✅

### F-002: TASK-P6-001 — 5 files
**Current:** Same pattern — scaffold + 2 models.

**Fix:** Same as F-001 — move `__init__.py`, `__manifest__.py` to `files_to_modify` since scaffold is `pre_completed`.

### F-003: TASK-P6-003 — 4 files
**Current:** `views/workflow_operations_dashboard.xml`, `views/workflow_retention_views.xml`, `views/menu_views.xml`, `__manifest__.py`

**Fix:** Move `__manifest__.py` to `files_to_modify` only (it already exists). Leaves 3 create + 1 modify = valid (constraint is on *create*).
- *Or:* Clarify constraint — if it means "total files touched" then split dashboard and retention views into 2 tasks.

---

## P2 — Medium: SDS §16 Files Not Covered

### F-004: `controllers/main.py` missing
SDS §16 lists `controllers/` in the core module file tree, but NO OMB section specifies a controller. This is a **spec gap in the OMB**, not an ITM gap per se.

**Action:** Add a task to P5 or P6 for `controllers/main.py` IF webhook/external endpoints need HTTP controllers. Otherwise flag as "deferred — no OMB spec."

### F-005: `static/description/icon.png` missing
Standard Odoo module compliance file — every module needs an icon.

**Action:** Add to TASK-P6-005 (OCA compliance) or TASK-P1-001 (scaffold). This is a trivial file.

---

## P3 — Low: Minor Items

### F-006: Task titles not GitHub-optimized
Some titles start with model names (e.g., `"workflow.instance model"`). For GitHub Issues, a verb-first title is more scannable (e.g., `"Implement workflow.instance model"`).

**Action:** Optional — add "Implement" or "Create" prefix to model task titles before GitHub issue creation.

### F-007: TASK-P6-006 spans two modules
Labels include both `"module:bpmn"` and `"module:operations"`, violating the module-scoped constraint.

**Action:** Split into two tasks (one per module) or assign to the primary module only.

---

## P2 — Medium: Business Logic Not Explicit in Acceptance Criteria

### F-008: 11 tasks use "All fields from OMB-01 §X" as acceptance criteria

The tasks **do** cover business logic — state machines (12 refs), methods (37 refs), constraints (35 refs). However, 11 model tasks delegate field specifics to "All fields from OMB-01 §X" without listing key business methods in acceptance criteria.

**Affected tasks:** TASK-P1-003, P1-004, P1-005, P1-006, P3-001, P3-002, P3-003, P3-004, P4-002, P4-003, P5-004

**Examples of what's covered vs. missing:**

| Task | Business Logic in AC | Missing from AC |
|---|---|---|
| TASK-P1-003 (version) | ✅ State machine, action_publish, action_archive, immutability | ✅ Adequate |
| TASK-P3-001 (instance) | ✅ State machine, advisory lock, action_cancel/recover | ⚠️ Missing: `_tick` engine algorithm, condition evaluation |
| TASK-P3-003 (token) | ⚠️ "Token never deleted", "split/join stubs" | ⚠️ Missing: `_advance`, `_consume`, fork/join logic |
| TASK-P4-002 (resolution) | ✅ `_resolve_approvers`, fallback logic | ⚠️ Missing: group vs user vs domain resolution detail |
| TASK-P5-003 (webhook) | ✅ HMAC-SHA256, retry policy, RFC-8785 | ✅ Adequate |

**Action:** Enhance acceptance criteria for the 5 tasks marked ⚠️ to explicitly list key business methods from OMB-01. Not a blocker — the OMB sections are authoritative and referenced — but better explicitness helps agents.

---

## Recommended Fixes (Priority Order)

| # | Severity | Fix | Effort |
|---|---|---|---|
| F-001 | P1 | Move scaffold files to `files_to_modify` in TASK-P3-007 | 2 min |
| F-002 | P1 | Move scaffold files to `files_to_modify` in TASK-P6-001 | 2 min |
| F-003 | P1 | Clarify TASK-P6-003 file count | 2 min |
| F-008 | P2 | Enhance 5 task acceptance criteria with key business methods | 10 min |
| F-005 | P2 | Add `icon.png` to TASK-P6-005 | 1 min |
| F-007 | P3 | Split TASK-P6-006 into 2 module-scoped tasks | 3 min |
| F-004 | P2 | Defer—no OMB spec for controllers | 0 min |
| F-006 | P3 | Optional title reformatting | 5 min |

**Total fix effort: ~25 minutes**
