provider "github" {
  owner = var.owner
}

module "repository" {
  source = "../modules/repository"

  repository_name = var.repository_name
  description     = var.repository_description
  visibility      = var.visibility
  default_branch  = var.default_branch
  topics          = var.topics

  has_issues   = true
  has_projects = false
  has_wiki     = false

  allow_squash_merge = true
  allow_merge_commit = false
  allow_rebase_merge = false

  allow_auto_merge    = true
  allow_update_branch = true

  delete_branch_on_merge = true
}
