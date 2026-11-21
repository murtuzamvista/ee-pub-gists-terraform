locals {
  supported_environments = ["local", "nonprod", "production"]
  is_local_environment   = terraform.workspace == "local" && var.environment == "local"
}

resource "helm_release" "argocd" {
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  version          = var.argocd_chart_version
  namespace        = "argocd"
  create_namespace = true
  timeout          = 900
  wait             = true

  values = [
    yamlencode({
      server = {
        service = {
          type = "ClusterIP"
        }
      }
      configs = {
        params = {
          "server.insecure" = true
        }
      }
    })
  ]

  lifecycle {
    precondition {
      condition     = contains(local.supported_environments, terraform.workspace)
      error_message = "Use one of the local, nonprod, or production Terraform workspaces."
    }

    precondition {
      condition     = var.environment == terraform.workspace
      error_message = "The environment in the selected tfvars file must match the Terraform workspace."
    }

    precondition {
      condition     = local.is_local_environment
      error_message = "Only the local environment is configured. EKS environments are placeholders and must not be applied yet."
    }

    precondition {
      condition     = var.kube_context == "kind-public-gists"
      error_message = "The local environment is pinned to the kind-public-gists Kubernetes context."
    }
  }
}
