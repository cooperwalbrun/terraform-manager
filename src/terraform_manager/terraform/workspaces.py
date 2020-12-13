import itertools
import os
from fnmatch import fnmatch
from typing import List, Optional, Dict, Any, Callable, Union, TypeVar

import requests
from requests import Response
from tabulate import tabulate
from terraform_manager.entities.error_response import ErrorResponse
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform import pagination, get_api_headers, SuccessHandler, ErrorHandler, \
    MESSAGE_COLUMN_CHARACTER_COUNT
from terraform_manager.utilities.throttle import throttle
from terraform_manager.utilities.utilities import safe_http_request, get_protocol, wrap_text, \
    is_empty

A = TypeVar("A")


def _map_workspaces(json: List[Dict[str, Any]]) -> List[Workspace]:
    required_attributes = [
        "name",
        "terraform-version",
        "auto-apply",
        "locked",
        "working-directory",
        "execution-mode",
        "speculative-enabled"
    ]

    def is_valid(json_object: Dict[str, Any]) -> bool:
        if "id" not in json_object or "attributes" not in json_object:
            return False
        else:
            for attribute in required_attributes:
                if attribute not in json_object["attributes"]:
                    return False
            return True

    workspaces = []
    for json_object in json:
        if is_valid(json_object):
            workspaces.append(
                Workspace(
                    json_object["id"],
                    json_object["attributes"]["name"],
                    json_object["attributes"]["terraform-version"],
                    json_object["attributes"]["auto-apply"],
                    json_object["attributes"]["locked"],
                    json_object["attributes"]["working-directory"],
                    json_object["attributes"]["execution-mode"],
                    json_object["attributes"]["speculative-enabled"]
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
    token: Optional[str] = None,
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
    :param token: A token suitable for authenticating against the Terraform API. If not specified, a
                  token will be searched for in the documented locations.
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
                token=token,
                write_error_messages=write_error_messages
            )
        ) if workspace_names is None or is_returnable(workspace)
    ]


def _internal_batch_operation(
    terraform_domain: str,
    workspaces: List[Workspace],
    *,
    json: Dict[str, Any],
    on_success: SuccessHandler[Workspace],
    on_failure: ErrorHandler[Workspace],
    no_tls: bool = False,
    token: Optional[str] = None,
    write_output: bool = False
) -> bool:
    headers = get_api_headers(terraform_domain, token=token, write_error_messages=write_output)
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


def batch_operation(
    terraform_domain: str,
    organization: str,
    workspaces: List[Workspace],
    *,
    field_mapper: Callable[[Workspace], A],
    field_name: str,
    new_value: A,
    report_only_value_mapper: Optional[Callable[[A], str]] = None,
    no_tls: bool = False,
    token: Optional[str] = None,
    write_output: bool = False
) -> bool:
    """
    Patches workspaces in batch fashion using a given JSON body, executing callback functions
    depending on the success or failure of each individual PATCH operation.

    :param terraform_domain: The domain corresponding to the targeted Terraform installation (either
                             Terraform Cloud or Enterprise).
    :param organization: The organization containing the workspaces to patch.
    :param workspaces: The workspaces to patch.
    :param field_mapper: A function which will be passed a Workspace object that must return a field
                         value to be compared against the new_value and printed in the tabulated
                         report.
    :param field_name: The Terraform API-compatible name of the field returned by field_mapper (e.g.
                       "auto-apply" instead of "auto apply" or "Auto Apply").
    :param new_value: The value to update the workspace field to (where the field corresponds to
                      field_name).
    :param report_only_value_mapper: A function which will be passed the result of the field_mapper
                                     function when writing the tabulated report's "Before" and
                                     "After" columns. If not specified, the default will be the
                                     str() function.
    :param no_tls: Whether to use SSL/TLS encryption when communicating with the Terraform API.
    :param token: A token suitable for authenticating against the Terraform API. If not specified, a
                  token will be searched for in the documented locations.
    :param write_output: Whether to print a tabulated result of the patch operations to STDOUT.
    :return: Whether all patch operations were successful. If even a single one failed, returns
             False.
    """

    json = {"data": {"type": "workspaces", "attributes": {field_name: new_value}}}
    report = []

    report_mapper = str if report_only_value_mapper is None else report_only_value_mapper

    def on_success(workspace: Workspace) -> None:
        report.append([
            workspace.name,
            report_mapper(field_mapper(workspace)),
            report_mapper(new_value),
            "success",
            f"{field_name} unchanged" if field_mapper(workspace) == new_value else "none"
        ])

    def on_failure(workspace: Workspace, response: Union[Response, ErrorResponse]) -> None:
        report.append([
            workspace.name,
            report_mapper(field_mapper(workspace)),
            report_mapper(field_mapper(workspace)),
            "error",
            wrap_text(str(response.json()), MESSAGE_COLUMN_CHARACTER_COUNT)
        ])

    result = _internal_batch_operation(
        terraform_domain,
        workspaces,
        json=json,
        on_success=on_success,
        on_failure=on_failure,
        no_tls=no_tls,
        token=token,
        write_output=write_output
    )

    if write_output:
        print((
            f'Terraform workspace {field_name} patch results for organization "{organization}" '
            f'at "{terraform_domain}":'
        ))
        print()
        print(
            tabulate(
                sorted(report, key=lambda x: (x[3], x[0])),
                headers=["Workspace", "Before", "After", "Status", "Message"]
            )
        )
        print()

    return result


def write_summary(
    terraform_domain: str,
    organization: str,
    workspaces: List[Workspace],
    *,
    targeting_specific_workspaces: bool,
    write_output: bool = False
) -> None:
    """
    Writes a tabulated summary of the workspaces' configuration to STDOUT. Only values in scope for
    terraform-manager will be written. Long lines will be wrapped automatically.

    :param terraform_domain: The domain corresponding to the targeted Terraform installation (either
                             Terraform Cloud or Enterprise).
    :param organization: The organization to which this data pertains.
    :param workspaces: The workspaces to report on.
    :param targeting_specific_workspaces: Whether one or more workspaces was specified in order to
                                          filter the list of workspaces when they were fetched.
    :param write_output: Whether to print the report to STDOUT. If this is False, this method is a
                         no-op.
    :return: None
    """

    if write_output:
        print((
            f'Terraform workspace summary for organization "{organization}" at '
            f'"{terraform_domain}":'
        ))
        print()

        report = []
        for workspace in workspaces:
            report.append([
                workspace.workspace_id,
                workspace.name,
                workspace.terraform_version,
                workspace.auto_apply,
                workspace.speculative,
                "<none>" if is_empty(workspace.working_directory) else workspace.working_directory,
                workspace.execution_mode,
                workspace.is_locked
            ])

        print(
            tabulate(
                sorted(report, key=lambda x: (x[1], x[0])),
                headers=[
                    "ID",
                    "Name",
                    "Version",
                    "Auto-Apply",
                    "Speculative",
                    "Working Directory",
                    "Execution Mode",
                    "Locked"
                ]
            )
        )

        if targeting_specific_workspaces:
            print()
            print(f"{os.linesep}Note: information is only being displayed for certain workspaces.")

        print()
