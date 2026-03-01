output "protected_branch" {
  description = "Protected branch pattern."
  value       = github_branch_protection.main.pattern
}

output "label_names" {
  description = "Managed label names."
  value       = sort(keys(github_issue_label.labels))
}
