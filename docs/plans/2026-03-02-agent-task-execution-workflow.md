# Agent Task Execution Workflow (Codex/Copilot/Antigravity)

Purpose: provide one clear, repeatable workflow for agents to pick a task, implement safely, open PR, handle review, and move to the next task.

## 0) Load This Workflow First (Mandatory)

- Read this file at the start of every new task before selecting files, creating a branch, or making edits.
- Treat this file as the default operational checklist for task execution.
- Any automation or shell command that starts a task must explicitly instruct the agent to read this file first.

## 0.1) Shell Bootstrap (Mandatory)

- Every task command in this workflow must run inside the workspace virtualenv at `/home/tunn/Documents/Odoo 19/venv`.
- Do not use system Python or a different virtualenv for task execution, verification, or helper scripts.
- Activate the workspace virtualenv once at the start of the shell session; all Python commands below assume it stays active.

```bash
source "/home/tunn/Documents/Odoo 19/venv/bin/activate"
which python
python --version
```

## 1) Preconditions

- `gh` CLI authenticated (`gh auth status`).
- Remote branch access to `tunneleven/odoo-dynamic-approval-workflow`.
- Odoo launcher available at repository parent (`./odoo.sh`).
- Workspace virtualenv available at `/home/tunn/Documents/Odoo 19/venv` and activated in the current shell.
- Work from a clean branch dedicated to one task.

## 2) Pick One Task

Preferred order:
1. Issue assigned to your agent label (`agent:codex`, `agent:copilot`, `agent:antigravity`).
2. Else issue labeled `agent:either`.
3. Only pick `status:todo` + `state:ready` tasks.

Command:

```bash
gh issue list --state open --limit 100 \
  --search "label:type:task label:status:todo label:state:ready"
```

Open selected issue and extract:
- `TASK-Px-yyy` ID
- GitHub issue number
- acceptance criteria
- dependencies
- files expected by ITM

```bash
gh issue view <issue_number> --json title,body,labels,url
```

Immediately record the issue number and carry it through to PR creation:

```bash
export ISSUE_NUMBER=<issue_number>
```

Rule:
- The same `ISSUE_NUMBER` from this step must be used in the PR body as the exact closing line `Closes #<issue_number>`.
- Do not create a PR that references only `TASK-P...` without the matching issue-closing keyword.

## 3) Start Branch

- Always branch from latest `main`.
- One task per branch.

```bash
git checkout main
git pull --ff-only
git checkout -b task-<task-id-lower>-<short-topic>
```

Examples:
- `task-p1-008-security-completion`
- `task-p3-006-runtime-record-rules`

## 4) Understand Scope Before Editing

Read in this order:
1. Issue body
2. `dynamic_approval_workflow/docs/design/itm_dynamic_approval_workflow.md`
3. Relevant OMB/SDS sections
4. Relevant SRS baseline/detailed sections when behavior, constraints, or acceptance intent is unclear
5. Existing model/security/view files that the issue touches

Rules:
- Do not expand scope beyond acceptance criteria.
- If task is already implemented, do not rework; document why and move to next actionable task.
- SRS is mandatory reference for requirement intent; OMB/SDS define implementation details.

## 5) Implement

- Change only files needed for this task.
- Keep naming and Odoo 19 patterns consistent.
- Avoid unrelated refactors in the same branch.

## 6) Verify Locally (Mandatory)

Run these checks before commit:

```bash
# Odoo 19 XML/API compatibility
python scripts/check_odoo19_compat.py

# Module install sanity
cd .. && ./odoo.sh -d test_<task_id_slug> -i dynamic_approval_core --stop-after-init --without-demo
```

If Python changed, also run:

```bash
python -m py_compile <changed_python_files>
```

If task includes tests, run targeted test tags/file.

## 7) Commit

- Stage only task-related files.
- Commit message should be short + scoped.

```bash
git add <changed_files>
git commit -m "<type>(<module>): <what changed>"
```

Examples:
- `security(core): complete phase-1 ACL and record-rule coverage`
- `test(core): tighten unique-constraint assertions and freeze datetimes`

## 8) Push and Open PR

**Hard gate before PR creation:**

- Always run a Codex code review on your branch diff before `gh pr create`.
- Resolve all critical/high findings first, or document a scope-based rationale in the PR body.

Suggested command:

```bash
codex run "Review current branch diff against main. Report findings only: bugs, regressions, risks, and missing tests, sorted by severity with file:line references." > /tmp/codex_review.md
```

Then proceed:

```bash
git push -u origin <branch_name>
```

PR body must include both:
- `Task ID: TASK-Px-yyy`
- Closing keyword: `Closes #<issue_number>`

Non-negotiable:
- The closing line must use the exact issue number from step 2.
- If the PR already exists without `Closes #<issue_number>`, edit the PR body immediately before continuing review work.

Template:

```markdown
Task ID: `TASK-Px-yyy`

## Summary
- item
- item

## Files Changed
- `path/file1`
- `path/file2`

## Verification
- `python scripts/check_odoo19_compat.py`
- `./odoo.sh -d test_<task> -i dynamic_approval_core --stop-after-init --without-demo`

Closes #<issue_number>
```

Create PR:

```bash
gh pr create --base main --head <branch_name> --title "[TASK-Px-yyy] <title>" --body-file /tmp/pr_body.md
```

## 9) CI and Metadata Guard

Immediately check:

```bash
gh pr view <pr_number> --json statusCheckRollup,mergeStateStatus,url
```

If `PR Metadata Guard` fails:
- Ensure PR body contains `TASK-P...` and `Closes #...` exactly.
- Edit PR body and re-check.
- Confirm the `Closes #...` issue number matches the task issue selected in step 2.

## 10) Handle Copilot Review (Required Loop)

Process every Copilot comment with this decision policy:

1. Analyze comment against:
- issue acceptance criteria
- ITM/OMB/SDS intent
- SRS requirement intent (when comment changes behavior/contract scope)
- current runtime behavior and tests

2. Decide:
- **Fix** if correctness, stability, maintainability, or guard compliance improves.
- **Counter-argue** if suggestion conflicts with repo policy/architecture or is lower-quality than current implementation.

3. Action:
- If fixing: patch, verify, commit, push.
- Reply directly on thread with rationale.
- Resolve thread after fix/decision is complete.

Useful queries:

```bash
# review + threads
gh api graphql -f query='query($owner:String!, $repo:String!, $number:Int!) { repository(owner:$owner,name:$repo){ pullRequest(number:$number){ reviewThreads(first:50){ nodes{ id isResolved isOutdated path line comments(first:20){ nodes{ databaseId author{login} body url } } } } } } }' -F owner=tunneleven -F repo=odoo-dynamic-approval-workflow -F number=<pr>
```

```bash
# reply to comment
gh api -X POST repos/tunneleven/odoo-dynamic-approval-workflow/pulls/<pr>/comments/<comment_id>/replies -f body='...'
```

```bash
# resolve thread
gh api graphql -f query='mutation($threadId:ID!){ resolveReviewThread(input:{threadId:$threadId}) { thread { id isResolved } } }' -F threadId='<thread_id>'
```

## 11) Merge Readiness Checklist

Before merge, confirm:
- All required checks success.
- No unresolved critical review threads.
- Codex pre-PR review was run and critical/high findings are resolved or explicitly justified.
- PR linked to issue via `Closes #...`.
- Scope matches original task only.
- Changes are aligned with SRS intent for the touched requirements.

## 12) After Merge

- Confirm issue label moved to review/done state via IssueOps.
- Return to step 2 and pick next `status:todo` + `state:ready` task.

---

## Quick Anti-Patterns

- Do not work directly on `main`.
- Do not mix two tasks in one branch/PR.
- Do not leave PR body without `TASK ID` + `Closes #...`.
- Do not assume the task ID alone will close the issue.
- Do not blindly accept/reject Copilot comments; always justify with repo context.
- Do not skip local verification before pushing.
- Do not run task commands outside `/home/tunn/Documents/Odoo 19/venv`.
