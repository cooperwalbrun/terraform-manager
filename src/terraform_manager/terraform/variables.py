import json
import os
import sys
from typing import List, Optional, Dict, Any, Callable, Union

import requests
from requests import Response
from tabulate import tabulate
from terraform_manager.entities.error_response import ErrorResponse
from terraform_manager.entities.variable import Variable
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform import get_api_headers, ErrorHandler, SuccessHandler
from terraform_manager.utilities.throttle import throttle
from terraform_manager.utilities.utilities import get_protocol, safe_http_request


def create_variables_template(*, write_output: bool = False) -> bool:
    """
    Writes an exemplary JSON file to the current directory.

    :param write_output: Whether to write informational messages to STDOUT and STDERR.
    :return: Whether the creation succeeded.
    """

    filename = "template.json"
    example = [
        Variable(key="key1", value="value1").to_json(),
        Variable(key="key2", value="value2").to_json()
    ]
    try:
        with open(filename, "w") as file:
            file.write(json.dumps(example, indent=2))
        if write_output:
            print(f"Successfully created {filename}.")
        return True
    except:
        if write_output:
            # yapf: disable
            print((
                f"Error: something went wrong while writing the {filename} file. Ensure you have "
                "permission to write files in the current working directory."
            ), file=sys.stderr)
            # yapf: enable
        return False


def parse_variables(file_path_and_name: str, write_output: bool = False) -> List[Variable]:
    """
    Parses Variable objects out of a given file.

    :param file_path_and_name: The path (relative to the current working directory) and filename of
                               the file containing the variables to configure.
    :param write_output: Whether to print a tabulated result of the patch operations to STDOUT.
    :return: A list of variables that were parsed from the given file, if any.
    """

    variables = []
    try:
        if os.path.exists(file_path_and_name):
            with open(file_path_and_name, "r") as file:
                variables_json = json.load(file)
            for obj in variables_json:
                variable = Variable.from_json(obj)
                if variable is not None:
                    variables.append(variable)
                else:
                    if write_output:
                        # yapf: disable
                        print((
                            "Warning: a variable was not successfully parsed from "
                            f"{file_path_and_name}. Its JSON is {json.dumps(obj)}"
                        ), file=sys.stderr)
                        # yapf: enable
            return variables
        else:
            raise ValueError(f"{file_path_and_name} does not exist.")
    except:
        if write_output:
            print(
                f"Error: unable to read and/or parse the {file_path_and_name} file into JSON.",
                file=sys.stderr
            )
        return variables


def _get_existing_variables(
    base_url: str,
    headers: Dict[str, str],
    workspace: Workspace,
    *,
    write_output: bool = False
) -> Optional[Dict[str, Variable]]:
    """
    Fetches the variables for a given workspaces.

    :param base_url: A URL fragment onto which a path will be appended to construct the Terraform
                     API endpoint.
    :param headers: The headers to provide in the API HTTP request to fetch the variables.
    :param workspace: The workspace for which variables will be fetched.
    :param write_output: Whether to print a tabulated result of the patch operations to STDOUT.
    :return: A dictionary mapping variable IDs to variables, or None if an error occurred.
    """
    def write_parse_error(json_object: Any) -> None:
        if write_output:
            print(
                f"Warning: a variable was not successfully parsed from {json.dumps(json_object)}",
                file=sys.stderr
            )

    # yapf: disable
    response = safe_http_request(
        lambda: throttle(lambda: requests.get(
            f"{base_url}/workspaces/{workspace.workspace_id}/vars",
            headers=headers
        ))
    )
    variables = {}
    # yapf: enable
    if response.status_code == 200:
        if "data" in response.json():
            for obj in response.json()["data"]:
                if "id" in obj and "attributes" in obj:
                    variable_id = obj["id"]
                    variable = Variable.from_json(obj["attributes"])
                    if variable is not None:
                        variables[variable_id] = variable
                    else:
                        write_parse_error(obj)
                        return None
                else:
                    write_parse_error(obj)
                    return None
    else:
        if write_output:
            print(
                f'Error: failed to get the existing variables for workspace "{workspace.name}".',
                file=sys.stderr
            )
        return None
    return variables


def _update_variables(
    base_url: str,
    headers: Dict[str, str],
    *,
    workspace: Workspace,
    updates: Dict[str, Variable],
    on_success: Callable[[Variable], None],
    on_failure: Callable[[Variable, Union[Response, ErrorResponse]], None]
) -> bool:
    """
    Fetches the variables for a given workspaces.

    :param base_url: A URL fragment onto which a path will be appended to construct the Terraform
                     API endpoint.
    :param headers: The headers to provide in the API HTTP request to fetch the variables.
    :param workspace: The workspace for which variables will be fetched.
    :param updates: A dictionary mapping variable IDs to the desired variable configurations
                    of those IDs.
    :param on_success: A function which will be passed a Variable object when that variable has
                       been successfully patched.
    :param on_failure: A function which will be passed a Variable object when that variable has
                       NOT been successfully patched.
    :return: Whether all HTTP operations were successful. If even a single one failed, returns
             False.
    """

    all_successful = True
    for variable_id, variable in updates.items():
        data = {"data": {"type": "vars", "id": variable_id, "attributes": variable.to_json()}}
        response = safe_http_request(
            lambda: throttle(
                lambda: requests.patch(
                    f"{base_url}/workspaces/{workspace.workspace_id}/vars/{variable_id}",
                    headers=headers,
                    json=data
                )
            )
        )
        if response.status_code == 200:
            on_success(variable)
        else:
            on_failure(variable, response)
            all_successful = False
    return all_successful


def _create_variables(
    base_url: str,
    headers: Dict[str, str],
    *,
    workspace: Workspace,
    creations: List[Variable],
    on_success: Callable[[Variable], None],
    on_failure: Callable[[Variable, Union[Response, ErrorResponse]], None]
) -> bool:
    """
    Fetches the variables for a given workspaces.

    :param base_url: A URL fragment onto which a path will be appended to construct the Terraform
                     API endpoint.
    :param headers: The headers to provide in the API HTTP request to fetch the variables.
    :param workspace: The workspace for which variables will be fetched.
    :param creations: A list of variables to be created.
    :param on_success: A function which will be passed a Variable object when that variable has
                       been successfully patched.
    :param on_failure: A function which will be passed a Variable object when that variable has
                       NOT been successfully patched.
    :return: Whether all HTTP operations were successful. If even a single one failed, returns
             False.
    """

    all_successful = True
    for variable in creations:
        data = {"data": {"type": "vars", "attributes": variable.to_json()}}
        response = safe_http_request(
            lambda: throttle(
                lambda: requests.post(
                    f"{base_url}/workspaces/{workspace.workspace_id}/vars",
                    headers=headers,
                    json=data
                )
            )
        )
        if response.status_code == 201:
            on_success(variable)
        else:
            on_failure(variable, response)
            all_successful = False
    return all_successful


def configure_variables(
    terraform_domain: str,
    organization: str,
    workspaces: List[Workspace],
    *,
    variables: List[Variable],
    no_tls: bool = False,
    token: Optional[str] = None,
    write_output: bool = False
) -> bool:
    """
    Creates or updates (in-place) one or more variables for the workspaces. If variables already
    exist with same keys, they will instead be updated so that all their fields equal the ones given
    in the variables passed to this method. This behavior allows this method to be idempotent.

    :param terraform_domain: The domain corresponding to the targeted Terraform installation (either
                             Terraform Cloud or Enterprise).
    :param organization: The organization containing the workspaces to patch.
    :param workspaces: The workspaces to patch.
    :param variables: The variables to either create or update.
    :param no_tls: Whether to use SSL/TLS encryption when communicating with the Terraform API.
    :param token: A token suitable for authenticating against the Terraform API. If not specified, a
                  token will be searched for in the documented locations.
    :param write_output: Whether to print a tabulated result of the patch operations to STDOUT.
    :return: Whether all HTTP operations were successful. If even a single one failed, returns
             False.
    """
    report = []

    def on_success(w: Workspace, create: bool) -> SuccessHandler[Variable]:
        operation = "create" if create else "update"

        def callback(v: Variable) -> None:
            report.append([w.name, v.key, operation, "success", ""])

        return callback

    def on_failure(w: Workspace, create: bool) -> ErrorHandler[Variable]:
        operation = "create" if create else "update"

        def callback(v: Variable, response: Union[Response, ErrorResponse]) -> None:
            report.append([w.name, v.key, operation, "error", response.json()])

        return callback

    headers = get_api_headers(terraform_domain, token=token, write_error_messages=write_output)
    base_url = f"{get_protocol(no_tls)}://{terraform_domain}/api/v2"
    all_successful = True
    for workspace in workspaces:
        updates_needed = {}
        creations_needed = []
        existing_variables = _get_existing_variables(
            base_url, headers, workspace, write_output=write_output
        )
        if existing_variables is None:  # Reminder: it will be none if something went wrong
            all_successful = False
            continue
        for new_variable in variables:
            needs_update = False
            for variable_id, old_variable in existing_variables.items():
                if old_variable.key == new_variable.key:
                    needs_update = True
                    updates_needed[variable_id] = new_variable
                    break
            if not needs_update:
                creations_needed.append(new_variable)
        all_successful = _create_variables(
            base_url,
            headers,
            workspace=workspace,
            creations=creations_needed,
            on_success=on_success(workspace, True),
            on_failure=on_failure(workspace, True)
        )
        all_successful = not all_successful or _update_variables(
            base_url,
            headers,
            workspace=workspace,
            updates=updates_needed,
            on_success=on_success(workspace, False),
            on_failure=on_failure(workspace, False)
        )

    if write_output:
        print((
            f'Terraform workspace variable configuration results for organization "{organization}" '
            f'at "{terraform_domain}":'
        ))
        print()
        print(
            tabulate(
                sorted(report, key=lambda x: (x[3], x[2], x[0], x[1])),
                headers=["Workspace", "Variable", "Operation", "Status", "Message"]
            )
        )
        print()

    return all_successful
