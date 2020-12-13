import sys
from typing import Optional, List

import semver
from terraform_manager.entities.terraform import Terraform
from terraform_manager.terraform import LATEST_VERSION, variables
from terraform_manager.terraform.variables import parse_variables


def _fallible(operation: bool) -> None:
    if not operation:
        # There is no need to write any error messages because a report and/or status messages
        # should be written by the "operation"
        fail()


def fail() -> None:
    sys.exit(1)


def validate(terraform: Terraform) -> bool:
    if len(terraform.workspaces) == 0:
        if terraform.workspace_names is not None:
            if terraform.write_output:
                names = ", ".join(terraform.workspace_names)
                print(
                    f"Error: no workspaces could be found with these name(s): {names}",
                    file=sys.stderr
                )
            return False
        else:
            if terraform.write_output:
                print("Error: no workspaces could be found in your organization.", file=sys.stderr)
            return False
    return True


def create_variables_template(silent: bool) -> None:
    _fallible(variables.create_variables_template(write_output=(not silent)))


def set_versions(terraform: Terraform, desired_version: Optional[str]) -> None:
    if not semver.VersionInfo.isvalid(desired_version) and desired_version != LATEST_VERSION:
        if terraform.write_output:
            print(
                f"Error: the version you specified ({desired_version}) is not valid.",
                file=sys.stderr
            )
        fail()
    else:
        _fallible(terraform.set_versions(desired_version))


def lock_or_unlock_workspaces(terraform: Terraform, lock: bool) -> None:
    _fallible(terraform.lock_workspaces() if lock else terraform.unlock_workspaces())


def set_working_directories(terraform: Terraform, working_directory: Optional[str]) -> None:
    _fallible(terraform.set_working_directories(working_directory))


def set_execution_modes(terraform: Terraform, execution_mode: str) -> None:
    arguments = execution_mode.split(",")
    if len(arguments) > 1:
        _fallible(terraform.set_execution_modes(arguments[0], agent_pool_id=arguments[1]))
    else:
        _fallible(terraform.set_execution_modes(execution_mode))


def set_auto_apply(terraform: Terraform, auto_apply: bool) -> None:
    _fallible(terraform.set_auto_apply(auto_apply))


def set_speculative(terraform: Terraform, speculative: bool) -> None:
    _fallible(terraform.set_speculative(speculative))


def configure_variables(terraform: Terraform, file: str) -> None:
    variables_to_configure = parse_variables(file, write_output=True)
    if len(variables_to_configure) == 0:
        if terraform.write_output:
            print(f"Error: no variable definitions found in {file}.", file=sys.stderr)
        fail()
    else:
        _fallible(terraform.configure_variables(variables_to_configure))


def delete_variables(terraform: Terraform, variable_keys: List[str]) -> None:
    _fallible(terraform.delete_variables(variable_keys))
