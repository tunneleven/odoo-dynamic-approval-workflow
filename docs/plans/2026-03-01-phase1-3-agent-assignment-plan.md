# Phase 1 Task Assignment Plan (3 Agents)

Date: 2026-03-01  
Scope: ITM Phase 1 (`TASK-P1-001` .. `TASK-P1-010`)  
Agents: `codex`, `copilot`, `antigravity`

## 1. Planning Objective

Deliver all Phase 1 tasks with minimum dependency wait time and controlled merge risk.

## 2. Dependency Summary

Critical dependency chain:

`P1-001 -> P1-002 -> P1-003 -> (P1-004, P1-005, P1-006) + P1-007 -> P1-008 -> P1-009 -> P1-010`

Current issue state snapshot:
- `#1` (`TASK-P1-001`) is already in review.
- `#2`..`#10` are open and todo.

## 3. Agent Roles

- `codex`: critical-path owner + integration/security gate.
- `copilot`: fast implementation on low/medium-coupling tasks + view layer.
- `antigravity`: model-heavy side branch + final tests.

## 4. Task-to-Agent Assignment

| Task | Issue | Owner | Why |
|---|---:|---|---|
| `TASK-P1-001` | #1 | codex (ongoing) | Foundation/security already active on Codex PR |
| `TASK-P1-002` | #2 | codex | Core base model, unlocks most downstream work |
| `TASK-P1-003` | #3 | codex | Version state machine is central dependency |
| `TASK-P1-004` | #4 | copilot | Small isolated model task |
| `TASK-P1-005` | #5 | antigravity | Medium model logic (`safe_eval`) can run in parallel wave |
| `TASK-P1-006` | #6 | copilot | Small policy model; parallel with #4/#5 |
| `TASK-P1-007` | #7 | antigravity | Independent from #2/#3 (depends only on #1) |
| `TASK-P1-008` | #8 | codex | ACL/rules integration depends on all model outputs |
| `TASK-P1-009` | #9 | copilot | View/menu assembly after security completion |
| `TASK-P1-010` | #10 | antigravity | Test closure task after UI/security complete |

## 5. Execution Waves

### Wave A (Start immediately after #1 merge)
- `codex` -> `#2`
- `antigravity` -> `#7`

### Wave B (after #2 merged)
- `codex` -> `#3`

### Wave C (after #3 merged)
- `copilot` -> `#4` and `#6`
- `antigravity` -> `#5`

### Wave D (after #4/#5/#6/#7 merged)
- `codex` -> `#8`

### Wave E (after #8 merged)
- `copilot` -> `#9`

### Wave F (after #9 merged)
- `antigravity` -> `#10`

## 6. Merge/Risk Controls

1. `models/__init__.py` is shared by many model tasks; keep one open PR per agent in Phase 1 to reduce rebase churn.
2. Require all Phase 1 PRs to include:
   - `TASK-P1-xxx` in PR body
   - `Closes #<issue>`
   - Odoo install verification output
3. Keep Copilot auto-review enabled and use `copilot-review-loop.yml` for response automation.
4. `TASK-P1-008` is integration gate: do not start until all dependent model PRs are merged.

## 7. Review Matrix

- PR authored by `codex` -> primary AI reviewer `copilot`, secondary `antigravity`.
- PR authored by `copilot` -> primary AI reviewer `codex`, secondary `antigravity`.
- PR authored by `antigravity` -> primary AI reviewer `codex`, secondary `copilot`.

## 8. Ready-to-Apply Label/Assignee Plan

- Add preferred agent labels:
  - `#2 #3 #8` -> `agent:codex`
  - `#4 #6 #9` -> `agent:copilot`
  - `#5 #7 #10` -> `agent:antigravity`

- Assign issue owner only when wave becomes active (avoid stale in-progress labels).
