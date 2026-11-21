variable "kubeconfig_path" {
  description = "Path to the kubeconfig used to manage Argo CD Applications."
  type        = string
  default     = "~/.kube/config"
}

variable "kube_context" {
  description = "Explicit Kubernetes context where Argo CD is installed."
  type        = string
  default     = "kind-public-gists"
}

variable "argocd_applications" {
  description = "Argo CD Applications keyed by a stable identifier."
  type = map(object({
    name       = string
    namespace  = string
    finalizers = list(string)
    project    = string
    gitops = object({
      repository = string
      revision   = string
      path       = string
    })
    destination = object({
      server    = string
      namespace = string
    })
    automated_sync = bool
    prune          = bool
    self_heal      = bool
  }))
}
