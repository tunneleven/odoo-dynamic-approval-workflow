# Dynamic Approval Workflow

Dynamic Approval Workflow project for Odoo 19.

## Repository Infrastructure

GitHub repository provisioning and governance are managed with Terraform in [`terraform/`](terraform/README.md).

Key defaults:
- Owner: `tunneleven`
- Repository: `odoo-dynamic-approval-workflow`
- Visibility: `public`
- State backend: local (`terraform.tfstate`)

## Automation Runbook

- Agent task auto-pick and Copilot review routing:
  - [`docs/plans/2026-03-01-agent-autopick-review-loop.md`](docs/plans/2026-03-01-agent-autopick-review-loop.md)
- Agent task execution workflow (pick → implement → commit → PR → review response):
  - [`docs/plans/2026-03-02-agent-task-execution-workflow.md`](docs/plans/2026-03-02-agent-task-execution-workflow.md)
- Monitoring script: `scripts/monitor_agent_queue.sh`
- systemd installer: `scripts/install_agent_worker_service.sh`
