import itertools
from fnmatch import fnmatch
from typing import List, Optional, Dict, Any, Callable, Union

import requests
from requests import Response
from terraform_manager.entities.error_response import ErrorResponse
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform import pagination, get_api_headers
from terraform_manager.utilities.throttle import throttle
from terraform_manager.utilities.utilities import safe_http_request, get_protocol


def _map_workspaces(json: List[Dict[str, Any]]) -> List[Workspace]:
    workspaces = []
    for json_object in json:
        if "id" in json_object and "attributes" in json_object and "name" in \
                json_object["attributes"] and "terraform-version" in json_object["attributes"] and \
                "auto-apply" in json_object["attributes"] and "locked" in \
                json_object["attributes"] and "working-directory" in json_object["attributes"]:
            workspaces.append(
                Workspace(
                    json_object["id"],
                    json_object["attributes"]["name"],
                    json_object["attributes"]["terraform-version"],
                    json_object["attributes"]["auto-apply"],
                    json_object["attributes"]["locked"],
                    json_object["attributes"]["working-directory"]
                )
            )
    return workspaces


def fetch_all(
    terraform_domain: str,
    organization: str,
    *,
    workspace_names: Optional[List[str]] = None,
    blacklist: bool = False,
    no_tls: bool = False,
    write_error_messages: bool = False
) -> List[Workspace]:
    """
    Fetch all workspaces (or a subset if desired) from a particular Terraform organization.

    :param terraform_domain: The domain corresponding to the targeted Terraform installation (either
                             Terraform Cloud or Enterprise).
    :param organization: The organization for which to fetch workspace data.
    :param workspace_names: The name(s) of workspace(s) for which data should be fetched. If not
                       specified, all workspace data will be fetched.
    :param blacklist: Whether to use the specified workspaces as a blacklist-style filter.
    :param no_tls: Whether to use SSL/TLS encryption when communicating with the Terraform API.
    :param write_error_messages: Whether to write error messages to STDERR.
    :return: The workspace objects corresponding to the given criteria.
    """

    lower_workspaces = [] if workspace_names is None else [
        workspace.lower() for workspace in workspace_names
    ]

    def is_returnable(workspace: Workspace) -> bool:
        for name in lower_workspaces:
            if fnmatch(workspace.name.lower(), name):
                return not blacklist
        return blacklist

    base_url = f"{get_protocol(no_tls)}://{terraform_domain}/api/v2"
    return [
        workspace for workspace in itertools.chain.from_iterable(
            pagination.exhaust_pages(
                f"{base_url}/organizations/{organization}/workspaces",
                json_mapper=_map_workspaces,
                write_error_messages=write_error_messages
            )
        ) if workspace_names is None or is_returnable(workspace)
    ]


def batch_operation(
    terraform_domain: str,
    workspaces: List[Workspace],
    *,
    json: Dict[str, Any],
    on_success: Callable[[Workspace], None],
    on_failure: Callable[[Workspace, Union[Response, ErrorResponse]], None],
    no_tls: bool = False,
    write_output: bool = False
) -> bool:
    """
    Patches workspaces in batch fashion using a given JSON body, executing callback functions
    depending on the success or failure of each individual PATCH operation.

    :param terraform_domain: The domain corresponding to the targeted Terraform installation (either
                             Terraform Cloud or Enterprise).
    :param workspaces: The workspaces to patch.
    :param json: The JSON body of the PATCH requests that will be sent to the Terraform API.
    :param on_success: A function which will be passed a workspace object when that workspace has
                       been successfully patched.
    :param on_failure: A function which will be passed a workspace object when that workspace has
                       not been successfully patched.
    :param no_tls: Whether to use SSL/TLS encryption when communicating with the Terraform API.
    :param write_output: Whether to print a tabulated result of the patch operations to STDOUT.
    :return: Whether all patch operations were successful. If even a single one failed, returns
             False.
    """

    headers = get_api_headers(terraform_domain, write_error_messages=write_output)
    all_successful = True
    base_url = f"{get_protocol(no_tls)}://{terraform_domain}/api/v2"
    for workspace in workspaces:
        url = f"{base_url}/workspaces/{workspace.workspace_id}"
        response = safe_http_request(
            lambda: throttle(lambda: requests.patch(url, json=json, headers=headers))
        )
        if response.status_code == 200:
            on_success(workspace)
        else:
            all_successful = False
            on_failure(workspace, response)
    return all_successful
