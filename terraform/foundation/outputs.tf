output "owner" {
  description = "Repository owner."
  value       = var.owner
}

output "repository_name" {
  description = "Created repository name."
  value       = module.repository.repository_name
}

output "repository_html_url" {
  description = "Repository URL."
  value       = module.repository.repository_html_url
}

output "default_branch" {
  description = "Default branch."
  value       = module.repository.default_branch
}
