# Terraform infrastructure and Argo CD applications

This repository separates reusable Terraform configuration from environment
inputs:

```text
terraform/
  infra/
  apps/
configs/
  infra/
    local/
    nonprod/
    production/
  apps/
    dev/
    qa/
    prod/
scripts/
  tf.py
```

- `terraform/infra` manages cluster-level infrastructure, beginning with Argo
  CD installation.
- `terraform/apps` manages Argo CD `Application` resources.
- `configs/<project>/<environment>` contains one or more JSON tfvars files for
  the matching project and environment. The wrapper passes all files in
  lexical order.
- `scripts/tf.py` runs Terraform `validate`, `plan`, or `apply` from the correct root
  with the selected environment's config.

Workload manifests and Kustomize overlays remain in the GitOps repository;
Terraform manages the infrastructure and Argo CD pointers only.

## Run Terraform

From the repository root:

```sh
python3 scripts/tf.py --operation=validate --env=local --project=infra
python3 scripts/tf.py --operation=plan --env=local --project=infra
python3 scripts/tf.py --operation=apply --env=local --project=infra
```

For the Argo CD dev Application:

```sh
python3 scripts/tf.py --operation=validate --env=dev --project=apps
python3 scripts/tf.py --operation=plan --env=dev --project=apps
python3 scripts/tf.py --operation=apply --env=dev --project=apps
```

`plan` and `apply` select or create a Terraform workspace matching `--env`.
`apply` requires confirmation unless `--auto-approve` is explicitly supplied,
for example after a CI/CD approval gate. Validate does not select a workspace.

Install Argo CD through the `infra` project before planning Argo CD
Applications, since their Kubernetes CRD must exist. The local infra
configuration targets the `kind-public-gists` context. Non-production and
production infra configs remain placeholders until their cluster credentials
and provider setup are implemented.

Local Terraform state is kept per project root and workspace. Do not commit
Terraform state or credentials.

## Pre-commit checks

Install the Git hook once per clone and run all checks manually with:

```sh
pre-commit install
pre-commit run --all-files
```

The hooks check JSON and whitespace, lint and format Python, format Terraform,
and validate both Terraform roots. Terraform validation initializes with the
backend disabled; it does not apply changes to a cluster.

## Terraform CI

The GitHub Actions workflow runs on pull requests to `main` and pushes to
`main`. It uses a self-hosted runner, runs the pre-commit checks, and invokes
`scripts/tf.py --operation=validate` for every configured project and
environment. Register and keep the laptop runner online for these checks.
The runner needs Python, Git, and network access to install the pre-commit
hooks; Terraform is installed by the workflow.

This workflow only performs formatting, linting, and Terraform validation. It
does not run `plan` or `apply`, and does not change Terraform state or cluster
resources. Because self-hosted runners execute repository code on your laptop,
the job is skipped for pull requests from forks; only run it for trusted
repository changes. Adding plan/apply automation will require a persistent
remote state backend, cluster credentials on the runner, and an approval
strategy.
