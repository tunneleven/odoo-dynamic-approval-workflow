# Plans Index

Version: `v1.0`
Status: `active`
Last Verified: `2026-03-06`

---

## 1. Purpose

Index of operational and implementation plan documents under `docs/plans/`.

Use this file to locate historical plans and execution workflows without loading every plan file.

## 2. Plan Catalog

| Plan File | Date | Scope | Status |
|---|---|---|---|
| `2026-03-01-github-repo-terraform-design.md` | 2026-03-01 | Terraform architecture for GitHub repository provisioning/governance | Historical reference |
| `2026-03-01-github-repo-terraform-implementation-plan.md` | 2026-03-01 | Terraform implementation steps | Historical reference |
| `2026-03-01-itm-issueops-execution.md` | 2026-03-01 | ITM-to-IssueOps execution flow and automation | Operational reference |
| `2026-03-01-phase1-3-agent-assignment-plan.md` | 2026-03-01 | Agent assignment strategy for Phase 1 tasks | Historical reference |
| `2026-03-01-agent-autopick-review-loop.md` | 2026-03-01 | Agent auto-pick and Copilot review feedback loop | Operational reference |
| `2026-03-02-agent-task-execution-workflow.md` | 2026-03-02 | Standard execution workflow for Codex/Copilot/Antigravity | Operational reference |

## 3. Usage Guidance

1. For day-to-day task execution flow, start with:
   - `2026-03-02-agent-task-execution-workflow.md`
2. For automation behavior (queue pickup/review routing), see:
   - `2026-03-01-agent-autopick-review-loop.md`
3. For ITM issue lifecycle and status automation, see:
   - `2026-03-01-itm-issueops-execution.md`
4. Terraform plans are historical unless current task explicitly targets `terraform/`.
