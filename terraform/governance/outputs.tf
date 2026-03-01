output "protected_branch" {
  description = "Protected branch pattern."
  value       = module.governance.protected_branch
}

output "label_names" {
  description = "Managed label names."
  value       = module.governance.label_names
}
