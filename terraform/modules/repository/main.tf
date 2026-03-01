resource "github_repository" "this" {
  name        = var.repository_name
  description = var.description
  visibility  = var.visibility

  auto_init = true

  homepage_url = var.homepage_url != "" ? var.homepage_url : null

  has_issues   = var.has_issues
  has_projects = var.has_projects
  has_wiki     = var.has_wiki

  allow_squash_merge = var.allow_squash_merge
  allow_merge_commit = var.allow_merge_commit
  allow_rebase_merge = var.allow_rebase_merge

  allow_auto_merge    = var.allow_auto_merge
  allow_update_branch = var.allow_update_branch

  delete_branch_on_merge = var.delete_branch_on_merge

  vulnerability_alerts = true

  topics = var.topics
}

resource "github_branch_default" "this" {
  repository = github_repository.this.name
  branch     = var.default_branch
  rename     = true
}
