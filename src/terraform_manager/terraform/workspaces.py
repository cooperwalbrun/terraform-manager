import itertools
import os
import sys
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
    coalesce, safe_deep_get

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

    def is_valid(data_json_object: Dict[str, Any]) -> bool:
        if "id" not in data_json_object or "attributes" not in data_json_object:
            return False
        else:
            return all(x in data_json_object["attributes"] for x in required_attributes)

    workspaces = []
    for json_object in json:
        if is_valid(json_object):
            agent_pool_id = safe_deep_get(
                json_object, ["relationships", "agent-pool", "data", "id"]
            )
            attributes = json_object["attributes"]
            workspaces.append(
                Workspace(
                    workspace_id=json_object["id"],
                    name=attributes["name"],
                    terraform_version=attributes["terraform-version"],
                    auto_apply=attributes["auto-apply"],
                    is_locked=attributes["locked"],
                    working_directory=attributes["working-directory"],
                    agent_pool_id=coalesce(agent_pool_id, ""),
                    execution_mode=attributes["execution-mode"],
                    speculative=attributes["speculative-enabled"]
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
    field_mappers: List[Callable[[Workspace], A]],
    field_names: List[str],
    new_values: List[A],
    report_only_value_mappers: Optional[List[Callable[[A], str]]] = None,
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
    :param field_mappers: One or more functions which will be passed a Workspace object that must
                         return a field value to be compared against the new_value and printed in
                         the tabulated report.
    :param field_names: One or more Terraform API-compatible names of the fields returned by
                        field_mappers (e.g. "auto-apply" instead of "auto apply" or "Auto Apply").
                        There must be one field name for each field mapper (and order matters).
    :param new_values: The values to update the workspace field to. There must be one new value for
                       each field name (and order matters).
    :param report_only_value_mappers: One or more functions which will be passed the result of the
                                      field_mappers function when writing the tabulated report's
                                      "Before" and "After" columns. There must be one report-only
                                      value mapper for each field mapper (and order matters). If not
                                      specified, the default will be the str() function for all
                                      fields.
    :param no_tls: Whether to use SSL/TLS encryption when communicating with the Terraform API.
    :param token: A token suitable for authenticating against the Terraform API. If not specified, a
                  token will be searched for in the documented locations.
    :param write_output: Whether to print a tabulated result of the patch operations to STDOUT.
    :return: Whether all patch operations were successful. If even a single one failed, returns
             False.
    """

    report_mappers = [
        str for _ in field_mappers
    ] if report_only_value_mappers is None else report_only_value_mappers

    if len(field_mappers) == 0 or len(field_mappers) != len(field_names) or \
            len(field_mappers) != len(new_values) or len(field_mappers) != len(report_mappers):
        if write_output:
            # yapf: disable
            print((
                "Error: invalid arguments passed to batch_operation. Ensure the number of elements "
                "specified for field_mappers, field_names, new_values, and "
                "report_only_value_mappers (if specified) match up."
            ), file=sys.stderr)
            # yapf: enable
        return False

    json = {
        "data": {
            "type": "workspaces",
            "attributes": {field_names[i]: new_values[i]
                           for i in range(len(field_names))}
        }
    }
    report = []

    def on_success(workspace: Workspace) -> None:
        for i in range(len(field_names)):
            report.append([
                workspace.name,
                field_names[i],
                report_mappers[i](field_mappers[i](workspace)),
                report_mappers[i](new_values[i]),
                "success",
                "value unchanged" if field_mappers[i](workspace) == new_values[i] else "none"
            ])

    def on_failure(workspace: Workspace, response: Union[Response, ErrorResponse]) -> None:
        for i in range(len(field_names)):
            report.append([
                workspace.name,
                field_names[i],
                report_mappers[i](field_mappers[i](workspace)),
                report_mappers[i](field_mappers[i](workspace)),
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
            f'Terraform workspace {"/".join(field_names)} patch results for organization '
            f'"{organization}" at "{terraform_domain}":'
        ))
        print()
        print(
            tabulate(
                sorted(report, key=lambda x: (x[4], x[0], x[1])),
                headers=["Workspace", "Field", "Before", "After", "Status", "Message"]
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
                workspace.name,
                workspace.terraform_version,
                workspace.is_locked,
                workspace.auto_apply,
                workspace.speculative,
                coalesce(workspace.working_directory, "<none>"),
                coalesce(workspace.agent_pool_id, "<none>"),
                workspace.execution_mode
            ])

        print(
            tabulate(
                sorted(report, key=lambda x: x[0]),
                headers=[
                    "Name",
                    "Version",
                    "Locked",
                    "Auto-Apply",
                    "Speculative",
                    "Working Directory",
                    "Agent Pool ID",
                    "Execution Mode"
                ]
            )
        )

        if targeting_specific_workspaces:
            print()
            print(f"{os.linesep}Note: information is only being displayed for certain workspaces.")

        print()
