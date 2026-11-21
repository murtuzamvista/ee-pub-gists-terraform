# Argo CD Applications

This Terraform root manages Argo CD `Application` resources. Workload
manifests, Kustomize overlays, and image tags remain in the GitOps repository;
Terraform manages only the Argo CD pointers to those paths.

Environment-specific inputs live under
`configs/argocd-applications/<environment>/`. Applications are supplied as a
map keyed by a stable identifier; Terraform creates one Argo CD Application
per map entry. Each entry groups the repository, revision, and overlay path
under `gitops`, and the target cluster and namespace under `destination`. The
Kubernetes provider context identifies the cluster hosting Argo CD;
`destination.server` identifies where Argo CD deploys workloads.

## Apply order

This root uses a separate Terraform state from the Argo CD installation root.
That separation is intentional: Terraform must discover the Argo CD
`Application` custom resource definition while planning this root.

1. Install Argo CD with the parent Terraform root and wait for its Helm release
   to complete.
2. Ensure the dev overlay in the GitOps repository has a published image tag.
3. Plan with the environment-specific values and review before applying. From
   the repository root, the wrapper initializes Terraform and selects or
   creates the matching `dev` workspace:

   ```sh
   python3 scripts/tf.py --operation=plan --env=dev --project=argocd-applications
   python3 scripts/tf.py --operation=apply --env=dev --project=argocd-applications
   ```

Terraform connects using the configured kubeconfig and context. The Application
is defined only in this Terraform root. No cluster changes are made until
`terraform apply` is explicitly run.

QA and production have their own config directories and Terraform workspaces.
If an environment has its own Argo CD installation in another cluster, use a
separate state and provider context for it.

The Application has Argo CD's resources finalizer. Destroying it through
Terraform can cause Argo CD to delete the workloads it manages; review any
destroy plan carefully.
