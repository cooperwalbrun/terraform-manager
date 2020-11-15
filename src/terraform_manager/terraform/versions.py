from typing import List, Dict

from terraform_manager.entities.workspace import Workspace


def group_by_version(workspaces: List[Workspace]) -> Dict[str, List[Workspace]]:
    """
    Groups a list of workspaces by those workspaces' Terraform versions.

    :param workspaces: The workspaces to segment into groups.
    :return: A dictionary whose keys are Terraform versions and whose values are lists of workspaces
             which have that version.
    """

    versions = {}
    for workspace in workspaces:
        if str(workspace.terraform_version) in versions:
            versions[str(workspace.terraform_version)].append(workspace)
        else:
            versions[str(workspace.terraform_version)] = [workspace]
    return versions
