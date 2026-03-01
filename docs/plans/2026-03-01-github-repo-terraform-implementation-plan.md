# Implementation Plan: GitHub Repository Terraform Stack

Date: 2026-03-01

## Steps

1. Scaffold `terraform/modules/repository` and `terraform/modules/governance`.
2. Scaffold `terraform/foundation` and `terraform/governance` root stacks with locked defaults.
3. Document operator workflow and token requirements in `terraform/README.md`.
4. Add Terraform CI validation workflow under `.github/workflows`.
5. Update ignore patterns for Terraform local state.
6. Run `terraform fmt` and `terraform validate` for both stacks.

## Success Criteria

- `terraform validate` passes for both stacks.
- Governance stack codifies branch protection and labels.
- Foundation stack codifies repository bootstrap and merge behavior.
