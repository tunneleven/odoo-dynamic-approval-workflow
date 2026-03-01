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
    "type:task" = {
      color       = "0052cc"
      description = "Work item from ITM manifest"
    }
    "type:model" = {
      color       = "5319e7"
      description = "Model implementation task"
    }
    "type:view" = {
      color       = "1d76db"
      description = "View implementation task"
    }
    "type:security" = {
      color       = "b60205"
      description = "Security implementation task"
    }
    "type:js" = {
      color       = "c5def5"
      description = "Frontend or JS implementation task"
    }
    "type:data" = {
      color       = "bfdadc"
      description = "Data, readme, or compliance task"
    }
    "type:test" = {
      color       = "0e8a16"
      description = "Test implementation task"
    }
    "phase:1" = {
      color       = "d4c5f9"
      description = "ITM Phase 1"
    }
    "phase:2" = {
      color       = "c5def5"
      description = "ITM Phase 2"
    }
    "phase:3" = {
      color       = "bfdadc"
      description = "ITM Phase 3"
    }
    "phase:4" = {
      color       = "f9d0c4"
      description = "ITM Phase 4"
    }
    "phase:5" = {
      color       = "fef2c0"
      description = "ITM Phase 5"
    }
    "phase:6" = {
      color       = "d4edd6"
      description = "ITM Phase 6"
    }
    "module:core" = {
      color       = "0366d6"
      description = "dynamic_approval_core module task"
    }
    "module:bpmn" = {
      color       = "6f42c1"
      description = "dynamic_approval_bpmn module task"
    }
    "module:operations" = {
      color       = "0b7285"
      description = "dynamic_approval_operations module task"
    }
    "size:S" = {
      color       = "0e8a16"
      description = "Small task (1-2h)"
    }
    "size:M" = {
      color       = "fbca04"
      description = "Medium task (3-5h)"
    }
    "size:L" = {
      color       = "b60205"
      description = "Large task (6-8h)"
    }
    "status:todo" = {
      color       = "1d76db"
      description = "Ready to be picked up"
    }
    "status:in-progress" = {
      color       = "fbca04"
      description = "Work in progress"
    }
    "status:in-review" = {
      color       = "5319e7"
      description = "PR open or under review"
    }
    "status:done" = {
      color       = "0e8a16"
      description = "Merged and completed"
    }
    "state:ready" = {
      color       = "0e8a16"
      description = "Ready for agent pickup"
    }
    "state:blocked" = {
      color       = "b60205"
      description = "Blocked by dependency or decision"
    }
    "agent:codex" = {
      color       = "0366d6"
      description = "Task preferred for Codex"
    }
    "agent:copilot" = {
      color       = "6f42c1"
      description = "Task preferred for GitHub Copilot"
    }
    "agent:antigravity" = {
      color       = "c2e0c6"
      description = "Task preferred for Antigravity"
    }
    "agent:either" = {
      color       = "bfdadc"
      description = "Task can be picked by any agent"
    }
  }
}
