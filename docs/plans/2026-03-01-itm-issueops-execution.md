# ITM IssueOps Execution Plan

Date: `2026-03-01`
Owner: `Tech Lead`
Status: `ready`

## Purpose

Operationalize `itm_dynamic_approval_workflow.md` so tasks are executable through GitHub Issues,
agent pickup labels, and automated status transitions tied to PR lifecycle.

## Added Artifacts

- `.github/ISSUE_TEMPLATE/itm-task.yml`
- `.github/pull_request_template.md`
- `.github/workflows/issueops-status-sync.yml`
- `.github/workflows/pr-metadata-guard.yml`
- `scripts/itm_export_tasks.py`
- `scripts/itm_create_issues.py`

## Operator Workflow

1. Export tasks from ITM to JSON:

```bash
python scripts/itm_export_tasks.py \
  --itm dynamic_approval_workflow/docs/design/itm_dynamic_approval_workflow.md \
  --out dynamic_approval_workflow/docs/design/itm_tasks.json
```

2. Dry-run issue creation:

```bash
python scripts/itm_create_issues.py \
  --in dynamic_approval_workflow/docs/design/itm_tasks.json \
  --repo tunneleven/odoo-dynamic-approval-workflow
```

3. Apply issue creation:

```bash
python scripts/itm_create_issues.py \
  --in dynamic_approval_workflow/docs/design/itm_tasks.json \
  --repo tunneleven/odoo-dynamic-approval-workflow \
  --apply
```

4. Ensure milestones exist (once per repository):

```bash
gh api repos/tunneleven/odoo-dynamic-approval-workflow/milestones -X POST -f title='Phase 1: Core Models + Security'
gh api repos/tunneleven/odoo-dynamic-approval-workflow/milestones -X POST -f title='Phase 2: Binding + Enforcement'
gh api repos/tunneleven/odoo-dynamic-approval-workflow/milestones -X POST -f title='Phase 3: BPMN + Runtime'
gh api repos/tunneleven/odoo-dynamic-approval-workflow/milestones -X POST -f title='Phase 4: Approver + Tasks + Signature'
gh api repos/tunneleven/odoo-dynamic-approval-workflow/milestones -X POST -f title='Phase 5: Access + Notifications + Webhooks'
gh api repos/tunneleven/odoo-dynamic-approval-workflow/milestones -X POST -f title='Phase 6: Ops + Contracts + Tests'
```

5. Route a task to agent by label:
- `agent:codex`
- `agent:copilot`
- `agent:antigravity`
- `agent:either`

6. Keep PR linkage strict:
- PR body must include `Closes #<issue>`
- PR body must include `TASK-Px-yyy`
- `PR Metadata Guard` workflow enforces both rules

## Status Automation Rules

- Issue opened/reopened -> `status:todo`, `state:ready`
- Issue assigned -> `status:in-progress`
- PR opened/ready/synchronized (with `Closes #<issue>`) -> `status:in-review`
- PR merged -> `status:done`
- Issue closed -> `status:done`

## Notes

- This workflow is GitHub-native and agent-agnostic, so Copilot, Codex, and Antigravity share the same task state model.
- Label creation is idempotent in the workflow; missing labels are auto-created.
