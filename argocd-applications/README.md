# Argo CD Applications

This Terraform root manages Argo CD `Application` resources. Workload
manifests, Kustomize overlays, and image tags remain in the GitOps repository;
Terraform manages only the Argo CD pointers to those paths.

The dev Application configuration is in `dev.tfvars.json`. Applications are
supplied as a map keyed by a stable identifier; Terraform creates one Argo CD
Application per map entry. This allows multiple Applications hosted by the
same Argo CD installation to be managed together. Each entry groups the
repository, revision, and overlay path under `gitops`, and the target cluster
and namespace under `destination`. The Kubernetes provider context identifies
the cluster hosting Argo CD; `destination.server` identifies where Argo CD
deploys workloads.

## Apply order

This root uses a separate Terraform state from the Argo CD installation root.
That separation is intentional: Terraform must discover the Argo CD
`Application` custom resource definition while planning this root.

1. Install Argo CD with the parent Terraform root and wait for its Helm release
   to complete.
2. Ensure the dev overlay in the GitOps repository has a published image tag.
3. Initialize this root and use its dedicated `dev` workspace:

   ```sh
   terraform -chdir=argocd-applications init
   terraform -chdir=argocd-applications workspace select dev \
     || terraform -chdir=argocd-applications workspace new dev
   ```

4. Plan with the environment-specific values and review before applying:

   ```sh
   terraform -chdir=argocd-applications plan -var-file=dev.tfvars.json
   terraform -chdir=argocd-applications apply -var-file=dev.tfvars.json
   ```

Terraform connects using the configured kubeconfig and context. The Application
is defined only in this Terraform root. No cluster changes are made until
`terraform apply` is explicitly run.

Add QA or production as another map entry when it is managed by this same Argo
CD installation. If an environment has its own Argo CD installation in another
cluster, use a separate Terraform workspace/state and provider context for it.

The Application has Argo CD's resources finalizer. Destroying it through
Terraform can cause Argo CD to delete the workloads it manages; review any
destroy plan carefully.
