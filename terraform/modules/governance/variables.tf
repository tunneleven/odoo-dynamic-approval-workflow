variable "repository_name" {
  description = "Repository name."
  type        = string
}

variable "protected_branch" {
  description = "Protected branch name or pattern."
  type        = string
  default     = "main"
}

variable "enforce_admins" {
  description = "Enforce branch protections for admins."
  type        = bool
  default     = true
}

variable "required_approving_review_count" {
  description = "Minimum required approving reviews."
  type        = number
  default     = 1

  validation {
    condition     = var.required_approving_review_count >= 0 && var.required_approving_review_count <= 6
    error_message = "required_approving_review_count must be between 0 and 6."
  }
}

variable "dismiss_stale_reviews" {
  description = "Dismiss stale approvals when new commits are pushed."
  type        = bool
  default     = true
}

variable "require_code_owner_reviews" {
  description = "Require CODEOWNERS review when applicable."
  type        = bool
  default     = false
}

variable "require_last_push_approval" {
  description = "Require someone other than the last pusher to approve."
  type        = bool
  default     = false
}

variable "require_conversation_resolution" {
  description = "Require resolved conversations before merge."
  type        = bool
  default     = true
}

variable "required_linear_history" {
  description = "Require linear history."
  type        = bool
  default     = true
}

variable "allows_deletions" {
  description = "Allow deletion of protected branch."
  type        = bool
  default     = false
}

variable "allows_force_pushes" {
  description = "Allow force pushes to protected branch."
  type        = bool
  default     = false
}

variable "require_strict_status_checks" {
  description = "Require branch to be up to date for status checks."
  type        = bool
  default     = true
}

variable "required_status_check_contexts" {
  description = "Optional status check contexts required before merge."
  type        = list(string)
  default     = []
}

variable "labels" {
  description = "Issue labels to manage in GitHub."
  type = map(object({
    color       = string
    description = string
  }))

  default = {
    bug = {
      color       = "d73a4a"
      description = "Something is not working"
    }
    enhancement = {
      color       = "a2eeef"
      description = "New feature or request"
    }
    documentation = {
      color       = "0075ca"
      description = "Documentation improvements"
    }
    chore = {
      color       = "cfd3d7"
      description = "Maintenance task"
    }
    security = {
      color       = "b60205"
      description = "Security-related work"
    }
    needs-triage = {
      color       = "fbca04"
      description = "Needs initial triage"
    }
    "priority:high" = {
      color       = "b60205"
      description = "High priority"
    }
    "priority:medium" = {
      color       = "d93f0b"
      description = "Medium priority"
    }
    "priority:low" = {
      color       = "0e8a16"
      description = "Low priority"
    }
  }
}
