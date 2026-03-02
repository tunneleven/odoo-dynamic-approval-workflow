# Agent Auto-Pick + Copilot Review Response Loop

## Objective

Automate two behaviors:
1. Pick available issues automatically and start work without manual per-task prompting.
2. Route Copilot review feedback back to an execution agent automatically.

## Implemented Components

### 1) GitHub Queue Router

File: `.github/workflows/agent-auto-pick.yml`

- Triggers: `issues` events, manual dispatch, and a 10-minute cron.
- Claims oldest ready issue per queue label:
  - `agent:codex`
  - `agent:copilot`
  - `agent:antigravity`
  - `agent:either` (round-robin assignment to configured assignees)
- On claim, workflow sets `status:in-progress` and removes `status:todo` directly.

### 2) Copilot Feedback Router

File: `.github/workflows/copilot-review-loop.yml`

- Triggers:
  - `pull_request_review` (`submitted`)
  - `pull_request_review_comment` (`created`)
- For Copilot `changes_requested` or inline comment events:
  - comment on PR with machine marker and response template
  - for inline comments, post an automatic thread reply acknowledging queueing
  - assign PR to `REVIEW_FIX_ASSIGNEE` (fallback: `CODEX_AGENT_ASSIGNEE`)
  - linked issue labels:
    - add: `status:in-progress`, `needs:review-fix`
    - remove: `status:in-review`, `status:todo`
- For Copilot approval:
  - linked issue labels:
    - add: `status:in-review`
    - remove: `status:in-progress`, `status:todo`, `needs:review-fix`

### 3) Local Agent Worker

File: `scripts/agent_queue_worker.py`

- Uses authenticated `gh` CLI.
- Polls and claims ready issues for one agent queue.
- Prioritizes already-assigned `needs:review-fix` work.
- Executes configurable task command (`--start-command`) with issue placeholders.
- Posts start/finish markers to issue comments for auditability.

## Required Repository Variables

Set in **GitHub repo -> Settings -> Secrets and variables -> Actions -> Variables**:

- `CODEX_AGENT_ASSIGNEE`
- `COPILOT_AGENT_ASSIGNEE`
- `ANTIGRAVITY_AGENT_ASSIGNEE`
- `REVIEW_FIX_ASSIGNEE`

Recommended defaults:
- `CODEX_AGENT_ASSIGNEE=tunneleven`
- `REVIEW_FIX_ASSIGNEE=tunneleven`

## Worker Usage

One-shot dry run:

```bash
python3 scripts/agent_queue_worker.py \
  --repo tunneleven/odoo-dynamic-approval-workflow \
  --agent codex \
  --assignee tunneleven \
  --include-either \
  --dry-run \
  --once
```

Continuous mode with task command:

```bash
python3 scripts/agent_queue_worker.py \
  --repo tunneleven/odoo-dynamic-approval-workflow \
  --agent codex \
  --assignee tunneleven \
  --include-either \
  --poll-seconds 90 \
  --start-command 'codex run "Resolve {task_id} from issue #{issue_number}: {issue_title}"'
```

Supported placeholders in `--start-command`:
- `{repo}`
- `{agent_mode}` (`new-task` or `review-fix`)
- `{issue_number}`
- `{issue_title}`
- `{issue_url}`
- `{task_id}`
- shell-escaped variants: `*_sh`

## Monitoring

Dashboard script:

```bash
./scripts/monitor_agent_queue.sh \
  --repo tunneleven/odoo-dynamic-approval-workflow \
  --agent codex \
  --assignee tunneleven
```

Watch mode (refresh every 15 seconds):

```bash
./scripts/monitor_agent_queue.sh \
  --repo tunneleven/odoo-dynamic-approval-workflow \
  --agent codex \
  --assignee tunneleven \
  --watch 15
```

## systemd User Service

Files:
- `deploy/systemd/agent-queue-worker.service.template`
- `deploy/systemd/agent-worker.env.example`
- `scripts/run_agent_worker.sh`
- `scripts/install_agent_worker_service.sh`

Install service:

```bash
./scripts/install_agent_worker_service.sh
```

Enable and start immediately:

```bash
./scripts/install_agent_worker_service.sh --enable-now
```

Check service and logs:

```bash
systemctl --user status agent-queue-worker.service
journalctl --user -u agent-queue-worker.service -f
```

## Validation Checklist

1. Create/open an issue labeled `status:todo`, `state:ready`, `agent:codex`, unassigned.
2. Confirm `Agent Auto Pick` assigns it automatically.
3. Confirm status becomes `status:in-progress`.
4. Open PR with `Closes #<issue>`.
5. Add Copilot review comment / request changes.
6. Confirm PR gets routing comment and linked issue receives `needs:review-fix`.
7. Confirm worker processes review-fix cycle and posts start/finish markers.
