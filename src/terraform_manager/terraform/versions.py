import os
from textwrap import wrap
from typing import List, Dict, Optional

from tabulate import tabulate
from terraform_manager.entities.workspace import Workspace
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


def patch_versions(organization: str, workspaces: List[Workspace], new_version: str) -> None:
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
