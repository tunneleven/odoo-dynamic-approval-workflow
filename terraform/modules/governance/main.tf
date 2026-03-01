resource "github_branch_protection" "main" {
  repository_id = var.repository_name
  pattern       = var.protected_branch

  enforce_admins = var.enforce_admins

  require_conversation_resolution = var.require_conversation_resolution
  required_linear_history         = var.required_linear_history

  allows_deletions    = var.allows_deletions
  allows_force_pushes = var.allows_force_pushes

  required_pull_request_reviews {
    dismiss_stale_reviews           = var.dismiss_stale_reviews
    require_code_owner_reviews      = var.require_code_owner_reviews
    required_approving_review_count = var.required_approving_review_count
    require_last_push_approval      = var.require_last_push_approval
  }

  dynamic "required_status_checks" {
    for_each = length(var.required_status_check_contexts) > 0 ? [1] : []
    content {
      strict   = var.require_strict_status_checks
      contexts = var.required_status_check_contexts
    }
  }
}

resource "github_issue_label" "labels" {
  for_each = var.labels

  repository  = var.repository_name
  name        = each.key
  color       = each.value.color
  description = each.value.description
}
