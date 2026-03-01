provider "github" {
  owner = var.owner
}

module "governance" {
  source = "../modules/governance"

  repository_name                 = var.repository_name
  protected_branch                = var.protected_branch
  required_approving_review_count = var.required_approving_review_count
  required_status_check_contexts  = var.required_status_check_contexts
  labels                          = var.labels

  enforce_admins                  = true
  dismiss_stale_reviews           = true
  require_code_owner_reviews      = false
  require_last_push_approval      = false
  require_conversation_resolution = true
  required_linear_history         = true
  allows_deletions                = false
  allows_force_pushes             = false
  require_strict_status_checks    = true
}
