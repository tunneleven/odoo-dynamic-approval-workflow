# Terraform: GitHub Repository Management

This folder manages GitHub repository bootstrap and governance for:
- Owner: `tunneleven`
- Repository: `odoo-dynamic-approval-workflow`
- Visibility: `public`
- State backend: local files (`terraform.tfstate`)

## Prerequisites

- Terraform `>= 1.6`
- GitHub token in environment:

```bash
export GITHUB_TOKEN="<token-with-repo-admin-rights>"
```

For public repository creation and settings, use a token that can:
- create/manage repositories under `tunneleven`
- manage branch protection rules
- manage labels

## Apply Order

1. Foundation stack (creates repository and default branch)
2. Governance stack (branch protection and labels)

## Foundation

```bash
cd terraform/foundation
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

## Governance

```bash
cd terraform/governance
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

## Notes

- Local state is intentionally used for single-operator simplicity.
- Keep `terraform.tfstate` and `terraform.tfvars` out of version control.
- Add required status checks later by setting `required_status_check_contexts` in governance tfvars.
