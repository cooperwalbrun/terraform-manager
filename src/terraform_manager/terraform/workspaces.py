import itertools
from typing import List, Optional, Dict, Any

from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform import pagination
from terraform_manager.utilities.utilities import coalesce_domain


def _map_workspaces(json: List[Dict[str, Any]]) -> List[Workspace]:
    workspaces = []
    for json_object in json:
        if "id" in json_object and "attributes" in json_object and "name" in \
                json_object["attributes"] and "terraform-version" in json_object["attributes"] and \
                "auto-apply" in json_object["attributes"] and "locked" in json_object["attributes"]:
            workspaces.append(
                Workspace(
                    json_object["id"],
                    json_object["attributes"]["name"],
                    json_object["attributes"]["terraform-version"],
                    json_object["attributes"]["auto-apply"],
                    json_object["attributes"]["locked"]
                )
            )
    return workspaces


def fetch_all(organization: str,
              workspaces: Optional[List[str]] = None,
              url: Optional[str] = None) -> List[Workspace]:
    """
    Fetch all workspace names (or a subset if desired) from a particular Terraform organization.

    :param organization: The organization for which to fetch workspace data.
    :param workspaces: The workspace(s) for which data should be fetched. If not specified, all
                       workspace data will be fetched.
    :param url: The URL of your target Terraform (e.g. Terraform Cloud or a custom Terraform
                Enterprise URL).
    :return: The workspace objects corresponding to the given criteria.
    """

    lower_workspaces = [] if workspaces is None else [workspace.lower() for workspace in workspaces]
    return [
        workspace for workspace in itertools.chain.from_iterable(
            pagination.exhaust_pages(
                f"https://{coalesce_domain(url)}/api/v2/organizations/{organization}/workspaces",
                _map_workspaces
            )
        ) if workspaces is None or workspace.name.lower() in lower_workspaces
    ]
