output "argocd_namespace" {
  description = "Namespace where Argo CD is installed."
  value       = helm_release.argocd.namespace
}

output "argocd_server_service" {
  description = "Service name to use for local port forwarding."
  value       = "argocd-server"
}
