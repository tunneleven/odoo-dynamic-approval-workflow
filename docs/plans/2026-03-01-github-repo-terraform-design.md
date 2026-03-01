# GitHub Repository + Terraform Design

Date: 2026-03-01  
Project: Dynamic Approval Workflow

## Context

This project currently has source and documentation locally, but no managed GitHub repository provisioning stack.
The goal is to create and govern a public GitHub repository using Terraform with local state files.

Locked decisions:
- Owner: `tunneleven`
- Repository: `odoo-dynamic-approval-workflow`
- Visibility: `public`
- Terraform state: local (`terraform.tfstate`)

## Architecture

Use a layered Terraform structure in one codebase:

- `terraform/foundation`: repository lifecycle and repository-level merge/default settings.
- `terraform/governance`: branch protection and issue labels.
- `terraform/modules/repository`: reusable repository creation module.
- `terraform/modules/governance`: reusable policy module.

Rationale:
- Keeps a single source of truth while separating creation from governance policy updates.
- Reduces operational risk compared to a monolithic stack.
- Makes branch policy evolution independent from repository bootstrap concerns.

## Components

Foundation provisions:
- `github_repository`
- `github_branch_default`

Governance provisions:
- `github_branch_protection` for `main`
- `github_issue_label` (managed via map)

Repository baseline:
- Public visibility
- Squash merge enabled
- Merge commit disabled
- Rebase merge disabled
- Auto-delete merged branches enabled

Branch protection baseline (`main`):
- PR required before merge
- Minimum 1 approval
- Dismiss stale approvals
- Resolve conversations before merge
- Enforce for admins
- Disallow force-push
- Disallow branch deletion

## Data Flow

1. Operator exports `GITHUB_TOKEN` (classic PAT or GitHub App token with appropriate repository admin rights).
2. Operator runs foundation stack (`init`, `plan`, `apply`).
3. Repository is created and default branch is set/renamed to `main`.
4. Operator runs governance stack (`init`, `plan`, `apply`).
5. Governance policies and labels are enforced as code.

## Error Handling and Safety

- Local state is kept per stack to avoid accidental cross-stack drift.
- GitHub API drift is surfaced by `terraform plan` before apply.
- Branch protection is applied only after repository creation by operational sequence (foundation first).
- No hardcoded credentials in code; authentication via environment variable.

## Testing and Verification

For each stack:
1. `terraform fmt -recursive`
2. `terraform init`
3. `terraform validate`
4. `terraform plan`

Post-apply checks on GitHub UI/API:
- Repository exists under `tunneleven/odoo-dynamic-approval-workflow`.
- Visibility is public.
- Default branch is `main`.
- Branch protection on `main` matches baseline.
- Labels are present with expected names/colors/descriptions.

## Out of Scope

- Team permissions and CODEOWNERS enforcement
- Rulesets beyond branch protection
- CI required status checks (left optional to avoid blocking initial bootstrap)

## Implementation Plan

- Create Terraform modules and layered root stacks.
- Add stack-specific `README` and `terraform.tfvars.example` files.
- Add CI workflow for Terraform format/validate checks.
- Update `.gitignore` for Terraform state and transient artifacts.
