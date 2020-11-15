import os
import sys
from textwrap import wrap
from typing import List, Dict, Optional

import requests
from tabulate import tabulate
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform import credentials
from terraform_manager.utilities.throttle import throttle
from terraform_manager.utilities.utilities import coalesce_domain

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


def patch_versions(
    organization: str, workspaces: List[Workspace], new_version: str, url: Optional[str]
) -> None:
    """
    Patches the Terraform version for each given workspace. This method will not attempt to patch
    any versions if at least one of the workspaces would be downgraded by the patch operation - this
    is prophylactic as Terraform itself does not support downgrades.

    :param organization: The organization whose workspaces are being patched.
    :param workspaces: The workspaces to patch.
    :param new_version: The new Terraform version to assign to the workspaces.
    :param url: The URL of the targeted Terraform (e.g. Terraform Cloud or a custom Terraform
                Enterprise URL).
    :return: None
    """

    for workspace in workspaces:
        if workspace.is_terraform_version_newer_than(new_version):
            # yapf: disable
            print((
                "Error: at least one of the target workspaces has a version newer than the one you "
                "are attempting to change to."
            ), file=sys.stderr)
            # yapf: enable
            sys.exit(1)
    headers = {"Authorization": f"Bearer {credentials.find_token(url)}"}
    data = {"data": {"attributes": {"terraform-version": new_version}}}
    for workspace in workspaces:
        url = f"https://{coalesce_domain(url)}/api/v2/workspaces/{workspace.workspace_id}",
        response = throttle(lambda: requests.patch(url, data=data, headers=headers))
        if response.status_code != 200:
            pass
        else:
            pass


def write_version_summary(
    organization: str,
    targeting_specific_workspaces: bool,
    url: Optional[str],
    data: VersionSummary
) -> None:
    """
    Writes a tabulated summary of the organization's workspaces and their versions to STDOUT. Long
    lines will be wrapped automatically.

    :param organization: The organization to which this data pertains.
    :param targeting_specific_workspaces: Whether one or more workspaces was specified on the
                                          command line, thereby filtering the data down.
    :param url: The URL of the targeted Terraform (e.g. Terraform Cloud or a custom Terraform
                Enterprise URL).
    :param data: The raw data to format and print to STDOUT.
    :return: None
    """

    domain = coalesce_domain(url)
    print(f'Terraform version summary for organization "{organization}" at "{domain}":{os.linesep}')
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
