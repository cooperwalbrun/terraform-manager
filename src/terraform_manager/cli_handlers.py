import sys
from typing import Optional, List

import semver
from terraform_manager.entities.terraform import Terraform
from terraform_manager.terraform import LATEST_VERSION, variables
from terraform_manager.terraform.variables import parse_variables


def _fallible(operation: bool) -> None:
    if not operation:
        # There is no need to write any error messages because a report should be written by the
        # "operation" lambda
        fail()


def fail() -> None:
    sys.exit(1)


def validate(terraform: Terraform) -> bool:
    if len(terraform.workspaces) == 0:
        if terraform.workspace_names is not None:
            names = ", ".join(terraform.workspace_names)
            print(
                f"Error: no workspaces could be found with these name(s): {names}", file=sys.stderr
            )
            return False
        else:
            print("Error: no workspaces could be found in your organization.", file=sys.stderr)
            return False
    return True


def create_variables_template() -> None:
    _fallible(variables.create_variables_template(write_output=True))


def patch_versions(terraform: Terraform, desired_version: Optional[str]) -> None:
    if not semver.VersionInfo.isvalid(desired_version) and desired_version != LATEST_VERSION:
        print(
            f"Error: the value for patch_versions you specified ({desired_version}) is not valid.",
            file=sys.stderr
        )
        fail()
    elif not terraform.check_versions(desired_version):
        # yapf: disable
        print((
            "Error: at least one of the target workspaces has a version newer than the one you are "
            "attempting to change to. No workspaces were updated."
        ), file=sys.stderr)
        # yapf: enable
        fail()
    else:
        _fallible(terraform.patch_versions(desired_version))


def lock_or_unlock_workspaces(terraform: Terraform, lock: bool) -> None:
    _fallible(terraform.lock_workspaces() if lock else terraform.unlock_workspaces())


def set_working_directories(terraform: Terraform, working_directory: Optional[str]) -> None:
    _fallible(terraform.set_working_directories(working_directory))


def configure_variables(terraform: Terraform, file: str) -> None:
    variables_to_configure = parse_variables(file, write_output=True)
    if len(variables_to_configure) == 0:
        print(f"Error: no variable definitions found in {file}.", file=sys.stderr)
        fail()
    else:
        _fallible(terraform.configure_variables(variables_to_configure))


def delete_variables(terraform: Terraform, variable_keys: List[str]) -> None:
    if len(variable_keys) == 0:
        print(f"Error: no variables specified for deletion.", file=sys.stderr)
        fail()
    else:
        _fallible(terraform.delete_variables(variable_keys))
