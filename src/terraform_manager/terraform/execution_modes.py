import sys
from typing import List, Optional, Union

from requests import Response
from tabulate import tabulate
from terraform_manager.entities.error_response import ErrorResponse
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform.workspaces import batch_operation


def patch_execution_modes(
    terraform_domain: str,
    organization: str,
    workspaces: List[Workspace],
    *,
    new_execution_mode: str,
    no_tls: bool = False,
    token: Optional[str] = None,
    write_output: bool = False
) -> bool:
    """
    Patches the execution modes of the workspaces.

    :param terraform_domain: The domain corresponding to the targeted Terraform installation (either
                             Terraform Cloud or Enterprise).
    :param organization: The organization containing the workspaces to patch.
    :param workspaces: The workspaces to patch.
    :param new_execution_mode: The new execution mode to assign to the workspaces. The value must be
                               either "remote", "local", or "agent" (case-sensitive).
    :param no_tls: Whether to use SSL/TLS encryption when communicating with the Terraform API.
    :param token: A token suitable for authenticating against the Terraform API. If not specified, a
                  token will be searched for in the documented locations.
    :param write_output: Whether to print a tabulated result of the patch operations to STDOUT.
    :return: Whether all patch operations were successful. If even a single one failed, returns
             False.
    """

    if new_execution_mode not in ["remote", "local", "agent"]:
        if write_output:
            print(f"Error: invalid execution-mode specified: {new_execution_mode}", file=sys.stderr)
        return False

    json = {"data": {"type": "workspaces", "attributes": {"execution-mode": new_execution_mode}}}
    report = []

    def on_success(workspace: Workspace) -> None:
        if workspace.execution_mode == new_execution_mode:
            report.append([
                workspace.name,
                workspace.execution_mode,
                new_execution_mode,
                "success",
                "execution mode unchanged"
            ])
        else:
            report.append([
                workspace.name, workspace.execution_mode, new_execution_mode, "success", "none"
            ])

    def on_failure(workspace: Workspace, response: Union[Response, ErrorResponse]) -> None:
        report.append([
            workspace.name,
            workspace.execution_mode,
            workspace.execution_mode,
            "error",
            response.json()
        ])

    result = batch_operation(
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
            f'Terraform workspace execution mode patch results for organization "{organization}" '
            f'at "{terraform_domain}":'
        ))
        print()
        print(
            tabulate(
                sorted(report, key=lambda x: (x[3], x[0])),
                headers=[
                    "Workspace",
                    "Execution Mode Before",
                    "Execution Mode After",
                    "Status",
                    "Message"
                ]
            )
        )
        print()

    return result
