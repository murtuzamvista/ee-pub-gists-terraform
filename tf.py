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


class TF:
    def __init__(self, repository_root: Path, project: str, environment: str) -> None:
        self.repository_root = repository_root.resolve()
        self.project = project
        self.environment = environment
        self.directory = self._find_project()

    def _find_project(self) -> Path:
        if self.project == "root":
            directory = self.repository_root
        else:
            if Path(self.project).name != self.project:
                raise ValueError("Project must be a Terraform root directly under the repository root.")
            directory = (self.repository_root / self.project).resolve()
            if directory.parent != self.repository_root:
                raise ValueError("Project must be a Terraform root directly under the repository root.")

        if not directory.is_dir() or not any(directory.glob("*.tf")):
            raise ValueError(f"Terraform project not found: {self.project}")
        return directory

    @property
    def variable_file(self) -> Path:
        return self.directory / f"{self.environment}.tfvars.json"

    def run(self, operation: str, auto_approve: bool = False) -> int:
        if not ENVIRONMENT_PATTERN.fullmatch(self.environment):
            raise ValueError("Environment may contain only letters, numbers, hyphens, and underscores.")
        if operation not in OPERATIONS:
            raise ValueError(f"Unsupported operation: {operation}")
        if auto_approve and operation != "apply":
            raise ValueError("--auto-approve can only be used with the apply operation.")

        result = self._run_terraform("init", "-input=false", *self._init_backend_args(operation))
        if result:
            return result

        if operation == "validate":
            return self._run_terraform("validate", "-no-color")

        if not self.variable_file.is_file():
            raise ValueError(
                f"Variable file not found for environment '{self.environment}' "
                f"and project '{self.project}': {self.variable_file}"
            )

        result = self._select_or_create_workspace()
        if result:
            return result

        arguments = [operation, "-input=false", f"-var-file={self.variable_file.name}"]
        if auto_approve:
            arguments.append("-auto-approve")
        return self._run_terraform(*arguments)

    @staticmethod
    def _init_backend_args(operation: str) -> tuple[str, ...]:
        if operation == "validate":
            return ("-backend=false",)
        return ()

    def _select_or_create_workspace(self) -> int:
        result = self._capture_terraform("workspace", "list", "-no-color")
        if result.returncode:
            return result.returncode

        workspaces = {
            line.strip().removeprefix("*").strip()
            for line in result.stdout.splitlines()
        }
        if self.environment in workspaces:
            return self._run_terraform("workspace", "select", self.environment)
        return self._run_terraform("workspace", "new", self.environment)

    def _run_terraform(self, *arguments: str) -> int:
        command = ["terraform", *arguments]
        print(f"+ {' '.join(command)}", flush=True)
        try:
            result = subprocess.run(command, cwd=self.directory, check=False)
        except FileNotFoundError:
            print("Error: Terraform executable not found on PATH.", file=sys.stderr)
            return 127
        return result.returncode

    def _capture_terraform(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        command = ["terraform", *arguments]
        print(f"+ {' '.join(command)}", flush=True)
        try:
            result = subprocess.run(
                command,
                cwd=self.directory,
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError as error:
            raise RuntimeError("Terraform executable not found on PATH.") from error
        if result.stdout:
            print(result.stdout, end="")
        if result.stderr:
            print(result.stderr, end="", file=sys.stderr)
        return result


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Terraform validate, plan, or apply for a project and environment."
    )
    parser.add_argument("--operation", choices=OPERATIONS, required=True)
    parser.add_argument("--env", required=True, help="Workspace and tfvars environment name.")
    parser.add_argument(
        "--project",
        required=True,
        help="Terraform root directory directly under this repository, or 'root'.",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Pass -auto-approve to Terraform apply. Intended for approved CI/CD jobs.",
    )
    return parser.parse_args()


def main() -> int:
    arguments = parse_arguments()
    repository_root = Path(__file__).resolve().parent
    try:
        project = TF(repository_root, arguments.project, arguments.env)
        return project.run(arguments.operation, arguments.auto_approve)
    except (ValueError, RuntimeError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
