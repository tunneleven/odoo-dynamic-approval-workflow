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

variable "repository_description" {
  description = "Repository description."
  type        = string
  default     = "Dynamic Approval Workflow for Odoo 19"
}

variable "visibility" {
  description = "Repository visibility."
  type        = string
  default     = "public"
}

variable "default_branch" {
  description = "Default branch name."
  type        = string
  default     = "main"
}

variable "topics" {
  description = "Repository topics."
  type        = list(string)
  default     = ["odoo", "odoo19", "approval-workflow", "agpl", "erp"]
}
