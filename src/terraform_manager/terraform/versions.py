import os
from textwrap import wrap
from typing import List, Dict

import requests
from tabulate import tabulate
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform import get_api_headers
from terraform_manager.utilities.throttle import throttle
from terraform_manager.utilities.utilities import safe_http_request

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


def patch_versions(
    terraform_domain: str,
    workspaces: List[Workspace],
    new_version: str,
    *,
    write_output: bool = False
) -> None:
    """
    Patches the Terraform version for each of a given list of workspaces.

    :param terraform_domain: The domain corresponding to the targeted Terraform installation (either
                             Terraform Cloud or Enterprise).
    :param workspaces: The workspaces to patch.
    :param new_version: The new Terraform version to assign to the workspaces.
    :param write_output: Whether to print a tabulated result of the patch operations to STDOUT.
    :return: None
    """

    json = {"data": {"type": "workspaces", "attributes": {"terraform-version": new_version}}}
    report = []
    headers = get_api_headers(terraform_domain, write_error_messages=write_output)
    for workspace in workspaces:
        url = f"https://{terraform_domain}/api/v2/workspaces/{workspace.workspace_id}"
        response = safe_http_request(
            lambda: throttle(lambda: requests.patch(url, json=json, headers=headers))
        )
        if response.status_code == 200:
            report.append([
                workspace.name, workspace.terraform_version, new_version, "success", "none"
            ])
        else:
            report.append([
                workspace.name,
                workspace.terraform_version,
                workspace.terraform_version,
                "error",
                response.json()
            ])
    if write_output:
        print(
            tabulate(
                sorted(report, key=lambda x: x[3]),
                headers=["Workspace", "Version Before", "Version After", "Status", "Message"],
                colalign=("left", "right", "right")
            )
        )


def write_version_summary(
    terraform_domain: str,
    organization: str,
    targeting_specific_workspaces: bool,
    data: VersionSummary
) -> None:
    """
    Writes a tabulated summary of the organization's workspaces and their versions to STDOUT. Long
    lines will be wrapped automatically.

    :param terraform_domain: The domain corresponding to the targeted Terraform installation (either
                             Terraform Cloud or Enterprise).
    :param organization: The organization to which this data pertains.
    :param targeting_specific_workspaces: Whether one or more workspaces was specified on the
                                          command line, thereby filtering the data down.
    :param data: The raw data to format and print to STDOUT.
    :return: None
    """

    print(f'Terraform version summary for organization "{organization}" at "{terraform_domain}":')
    print()
    if len(data) != 1 or targeting_specific_workspaces:
        table_data = []
        for version, workspaces in data.items():
            formatted_workspaces = ", ".join(sorted([workspace.name for workspace in workspaces]))
            formatted_workspaces = os.linesep.join(
                wrap(formatted_workspaces, width=70, break_long_words=False)
            )
            table_data.append([version, formatted_workspaces])
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
