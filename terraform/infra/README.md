# Cluster infrastructure Terraform

This Terraform root installs Argo CD with the HashiCorp Helm provider. The
`local` environment is configured for the `kind-public-gists` context.
`nonprod` and `production` have placeholder variable files only; EKS provider
configuration and deployments are not implemented yet.

## Deploy locally

Terraform and Python 3 must be installed, and the `kind-public-gists` cluster
must be running and present in `~/.kube/config`. Run the wrapper from the
repository root:

```sh
python3 scripts/tf.py --operation=plan --env=local --project=infra
python3 scripts/tf.py --operation=apply --env=local --project=infra
```

The wrapper supports `validate`, `plan`, and `apply`. It initializes Terraform,
selects or creates the environment workspace for plan/apply, and supplies
`<env>.tfvars.json` from the chosen project. Validation initializes without a
backend and does not select a workspace. Apply requires interactive approval by
default.

For CI/CD, run `plan` and then `apply` only after the pipeline's approval gate.
The apply operation can be made non-interactive explicitly:

```sh
python3 scripts/tf.py --operation=apply --env=local --project=infra --auto-approve
```

Environment-specific inputs are in `configs/infra/<environment>/`.

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

The `nonprod` and `production` configurations are placeholders. Their plans
intentionally fail the local-only precondition until EKS provider
authentication, cluster contexts, and environment-specific safeguards are
implemented.
