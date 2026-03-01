variable "repository_name" {
  description = "Repository name."
  type        = string
}

variable "description" {
  description = "Repository description."
  type        = string
  default     = "Dynamic Approval Workflow for Odoo 19"
}

variable "visibility" {
  description = "Repository visibility."
  type        = string
  default     = "public"

  validation {
    condition     = contains(["public", "private", "internal"], var.visibility)
    error_message = "visibility must be one of: public, private, internal."
  }
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

variable "homepage_url" {
  description = "Optional repository homepage URL."
  type        = string
  default     = ""
}

variable "has_issues" {
  description = "Enable issues."
  type        = bool
  default     = true
}

variable "has_projects" {
  description = "Enable projects."
  type        = bool
  default     = false
}

variable "has_wiki" {
  description = "Enable wiki."
  type        = bool
  default     = false
}

variable "allow_squash_merge" {
  description = "Allow squash merges."
  type        = bool
  default     = true
}

variable "allow_merge_commit" {
  description = "Allow merge commits."
  type        = bool
  default     = false
}

variable "allow_rebase_merge" {
  description = "Allow rebase merges."
  type        = bool
  default     = false
}

variable "allow_auto_merge" {
  description = "Allow auto-merge on pull requests."
  type        = bool
  default     = true
}

variable "allow_update_branch" {
  description = "Allow update branch suggestions on pull requests."
  type        = bool
  default     = true
}

variable "delete_branch_on_merge" {
  description = "Delete source branch after merge."
  type        = bool
  default     = true
}
