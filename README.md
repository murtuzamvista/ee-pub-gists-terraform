# Argo CD Terraform deployment

This Terraform root installs Argo CD with the HashiCorp Helm provider. The
`local` environment is configured for the `kind-public-gists` context.
`non-prod` and `prod` have placeholder variable files only; EKS provider
configuration and deployments are not implemented yet.

## Deploy locally

Run these commands from this directory. Terraform must be installed, and the
`kind-public-gists` cluster must be running and present in `~/.kube/config`.

```sh
terraform init
terraform workspace select local || terraform workspace new local
terraform plan -var-file=local.tfvars.json
terraform apply -var-file=local.tfvars.json
```

The Helm release creates the `argocd` namespace. The server stays on a
`ClusterIP`, so it is not exposed outside the cluster. For local access, run:

```sh
kubectl --context kind-public-gists -n argocd port-forward svc/argocd-server 8080:80
```

Open `http://localhost:8080`. Retrieve the initial admin password with:

```sh
kubectl --context kind-public-gists -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 --decode
```

## Manage Argo CD Applications

Argo CD Applications are managed as Terraform resources in the separate
`argocd-applications/` root. Application-specific settings are provided through
environment-specific values files. Apply the Argo CD installation first, then
select the corresponding workspace and review/apply the Application:

```sh
terraform -chdir=argocd-applications init
terraform -chdir=argocd-applications workspace select dev \
  || terraform -chdir=argocd-applications workspace new dev
terraform -chdir=argocd-applications plan -var-file=dev.tfvars.json
terraform -chdir=argocd-applications apply -var-file=dev.tfvars.json
```

The Application root uses its own Terraform state and manages the dev
Application only. It requires Argo CD's Application CRD to exist before
planning. For each additional environment, add a matching values file and use
a separate workspace. Workload manifests and overlays remain in the GitOps
repository. Review `argocd-applications/README.md` before applying, especially the
destroy behavior.

## Environment workspaces

Create the EKS workspaces when needed, but do not apply them until their
cluster contexts and EKS connectivity are configured:

```sh
terraform workspace new non-prod
terraform workspace new prod
```

Select the matching workspace and variable file together for every plan/apply:

```sh
terraform workspace select non-prod
terraform plan -var-file=non-prod.tfvars.json

terraform workspace select prod
terraform plan -var-file=prod.tfvars.json
```

The non-prod and prod plans intentionally fail a precondition for now. Replace
their placeholder context values and add the EKS-specific provider
authentication/configuration before implementing those environments.
