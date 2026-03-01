output "repository_name" {
  description = "Repository name."
  value       = github_repository.this.name
}

output "repository_node_id" {
  description = "Repository node ID."
  value       = github_repository.this.node_id
}

output "repository_html_url" {
  description = "Repository HTML URL."
  value       = github_repository.this.html_url
}

output "default_branch" {
  description = "Configured default branch."
  value       = github_branch_default.this.branch
}
