import os
import textwrap
from typing import List, Dict

from tabulate import tabulate
from terraform_manager.entities.workspace import Workspace
from terraform_manager.utilities.utilities import wrap_text

VersionSummary = Dict[str, List[Workspace]]


def group_by_version(workspaces: List[Workspace]) -> VersionSummary:
    """
    Groups a list of workspaces by those workspaces' Terraform versions.

    :param workspaces: The workspaces to segment into groups.
    :return: A dictionary whose keys are Terraform versions and whose values are lists of workspaces
             which have that version.
    """

    versions = {}
    for workspace in workspaces:
        if workspace.terraform_version in versions:
            versions[workspace.terraform_version].append(workspace)
        else:
            versions[workspace.terraform_version] = [workspace]
    return versions


def check_versions(workspaces: List[Workspace], new_version: str) -> bool:
    """
    Asserts whether at least one of the workspaces would be downgraded by a patch operation
    involving a given version - this is prophylactic as Terraform itself does not support
    downgrades.

    :param workspaces: The workspaces to check.
    :param new_version: The new Terraform version to check against the workspaces' versions.
    :return: Whether there are any workspaces which would be downgraded by patching to the new
             version.
    """

    for workspace in workspaces:
        if workspace.is_terraform_version_newer_than(new_version):
            return False
    return True


def write_version_summary(
    terraform_domain: str,
    organization: str,
    *,
    targeting_specific_workspaces: bool,
    data: VersionSummary,
    write_output: bool = False
) -> None:
    """
    Writes a tabulated summary of the workspaces and their versions to STDOUT. Long lines will be
    wrapped automatically.

    :param terraform_domain: The domain corresponding to the targeted Terraform installation (either
                             Terraform Cloud or Enterprise).
    :param organization: The organization to which this data pertains.
    :param targeting_specific_workspaces: Whether one or more workspaces was specified in order to
                                          filter the list of workspaces when they were fetched.
    :param data: The raw data to format and print to STDOUT.
    :param write_output: Whether to print a tabulated report to STDOUT.
    :return: None
    """

    if write_output:
        print(
            f'Terraform version summary for organization "{organization}" at "{terraform_domain}":'
        )
        print()
        if len(data) != 1 or targeting_specific_workspaces:
            table_data = []
            for version, workspaces in data.items():
                formatted_workspaces = ", ".join(
                    sorted([workspace.name for workspace in workspaces])
                )
                table_data.append([version, wrap_text(formatted_workspaces, 80)])
        else:
            table_data = [[list(data.keys())[0], "All"]]
        print(
            tabulate(
                sorted(table_data, key=lambda x: x[0], reverse=True),
                headers=["Version", "Workspaces"],
                colalign=("right", )
            )
        )
        if targeting_specific_workspaces:
            print(f"{os.linesep}Note: information is only being displayed for certain workspaces.")

        print()
