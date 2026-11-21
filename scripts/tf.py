#!/usr/bin/env python3
"""Run Terraform validate, plan, and apply for a project and environment."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


OPERATIONS = ("validate", "plan", "apply")
ENVIRONMENT_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]*\Z")
PROJECTS = ("infra", "argocd-applications")


class TF:
    def __init__(self, repository_root: Path, project: str, environment: str) -> None:
        self.repository_root = repository_root.resolve()
        self.project = project
        self.environment = environment
        if not ENVIRONMENT_PATTERN.fullmatch(environment):
            raise ValueError("Environment may contain only letters, numbers, hyphens, and underscores.")
        if project not in PROJECTS:
            raise ValueError(f"Project must be one of: {', '.join(PROJECTS)}")
        self.terraform_directory = self.repository_root / "terraform" / project
        self.config_directory = self.repository_root / "configs" / project / environment
        if not self.terraform_directory.is_dir() or not any(
            self.terraform_directory.glob("*.tf")
        ):
            raise ValueError(f"Terraform project not found: {self.terraform_directory}")
        if not self.config_directory.is_dir():
            raise ValueError(f"Environment config directory not found: {self.config_directory}")
        self.variable_files = self.find_variable_files()

    def find_variable_files(self) -> list[Path]:
        """Find the environment's variable files in a stable order."""
        variable_files = sorted(self.config_directory.glob("*.tfvars.json"))
        if not variable_files:
            raise ValueError(f"No .tfvars.json files found in {self.config_directory}")
        return variable_files

    def run(self, operation: str, auto_approve: bool = False) -> int:
        if operation not in OPERATIONS:
            raise ValueError(f"Unsupported operation: {operation}")
        if auto_approve and operation != "apply":
            raise ValueError("--auto-approve can only be used with the apply operation.")

        print("=== Terraform deployment ===")
        print(f"Project: {self.project}")
        print(f"Environment: {self.environment}")
        print(f"Operation: {operation}")
        print(f"Terraform directory: {self.terraform_directory}")
        print(f"Configuration directory: {self.config_directory}")

        result = self._run_terraform(
            "init", "-input=false", *self._init_backend_args(operation)
        )
        if result:
            return result

        if operation == "validate":
            return self._run_terraform("validate", "-no-color")

        result = self._select_or_create_workspace()
        if result:
            return result

        arguments = [operation, "-input=false"]
        arguments.extend(
            f"-var-file={Path('..', '..', 'configs', self.project, self.environment, path.name)}"
            for path in self.variable_files
        )
        if auto_approve:
            arguments.append("-auto-approve")
        return self._run_terraform(*arguments)

    @staticmethod
    def _init_backend_args(operation: str) -> tuple[str, ...]:
        if operation == "validate":
            return ("-backend=false",)
        return ()

    def _select_or_create_workspace(self) -> int:
        return self._run_terraform(
            "workspace", "select", "-or-create", self.environment
        )

    def _run_terraform(self, *arguments: str) -> int:
        command = ["terraform", *arguments]
        print(f"+ {' '.join(command)}", flush=True)
        try:
            result = subprocess.run(command, cwd=self.terraform_directory, check=False)
        except FileNotFoundError:
            print("Error: Terraform executable not found on PATH.", file=sys.stderr)
            return 127
        return result.returncode


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Terraform validate, plan, or apply for a project and environment."
    )
    parser.add_argument("--operation", choices=OPERATIONS, required=True)
    parser.add_argument("--env", required=True, help="Workspace and tfvars environment name.")
    parser.add_argument(
        "--project",
        required=True,
        choices=PROJECTS,
        help="Terraform project layer.",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Pass -auto-approve to Terraform apply. Intended for approved CI/CD jobs.",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    repository_root = Path(__file__).resolve().parents[1]
    try:
        project = TF(repository_root, arguments.project, arguments.env)
        return project.run(arguments.operation, arguments.auto_approve)
    except (ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
