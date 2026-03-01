variable "owner" {
  description = "GitHub organization or user account owning the repository."
  type        = string
  default     = "tunneleven"
}

variable "repository_name" {
  description = "Repository name."
  type        = string
  default     = "odoo-dynamic-approval-workflow"
}

variable "protected_branch" {
  description = "Protected branch name or pattern."
  type        = string
  default     = "main"
}

variable "required_approving_review_count" {
  description = "Minimum required approving reviews."
  type        = number
  default     = 1
}

variable "required_status_check_contexts" {
  description = "Optional required status check contexts."
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
