variable "environment" {
  description = "Environment name; must match the selected Terraform workspace."
  type        = string
}

variable "kubeconfig_path" {
  description = "Path to the kubeconfig used by the Helm provider."
  type        = string
  default     = "~/.kube/config"
}

variable "kube_context" {
  description = "Explicit Kubernetes context to prevent deploying to the current context by accident."
  type        = string
}

variable "argocd_chart_version" {
  description = "Pinned version of the Argo CD Helm chart."
  type        = string
}
