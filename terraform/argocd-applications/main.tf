resource "kubernetes_manifest" "application" {
  for_each = var.argocd_applications

  manifest = {
    apiVersion = "argoproj.io/v1alpha1"
    kind       = "Application"

    metadata = {
      name       = each.value.name
      namespace  = each.value.namespace
      finalizers = each.value.finalizers
    }

    spec = {
      project = each.value.project

      source = {
        repoURL        = each.value.gitops.repository
        targetRevision = each.value.gitops.revision
        path           = each.value.gitops.path
      }

      destination = {
        server    = each.value.destination.server
        namespace = each.value.destination.namespace
      }

      syncPolicy = each.value.automated_sync ? {
        automated = {
          prune    = each.value.prune
          selfHeal = each.value.self_heal
        }
      } : null
    }
  }
}
