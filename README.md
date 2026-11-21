# Argo CD Terraform deployment

This Terraform root installs Argo CD with the HashiCorp Helm provider. The
`local` environment is configured for the `kind-public-gists` context.
`non-prod` and `prod` have placeholder variable files only; EKS provider
configuration and deployments are not implemented yet.

## Deploy locally

Terraform and Python 3 must be installed, and the `kind-public-gists` cluster
must be running and present in `~/.kube/config`.

```sh
python3 tf.py --operation=plan --env=local --project=root
python3 tf.py --operation=apply --env=local --project=root
```

The wrapper supports `validate`, `plan`, and `apply`. It initializes Terraform,
selects or creates the environment workspace for plan/apply, and supplies
`<env>.tfvars.json` from the chosen project. Validation initializes without a
backend and does not select a workspace. Apply requires interactive approval by
default.

For CI/CD, run `plan` and then `apply` only after the pipeline's approval gate.
The apply operation can be made non-interactive explicitly:

```sh
python3 tf.py --operation=apply --env=local --project=root --auto-approve
```

Use `--project=argocd-applications` for the Argo CD Application Terraform root.

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
python3 tf.py --operation=plan --env=dev --project=argocd-applications
python3 tf.py --operation=apply --env=dev --project=argocd-applications
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
