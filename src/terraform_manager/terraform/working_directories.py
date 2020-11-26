from typing import List, Union, Optional

from requests import Response
from tabulate import tabulate
from terraform_manager.entities.error_response import ErrorResponse
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform.workspaces import batch_operation


def patch_working_directories(
    terraform_domain: str,
    organization: str,
    workspaces: List[Workspace],
    *,
    new_working_directory: Optional[str],
    no_tls: bool = False,
    write_output: bool = False
) -> bool:
    """
    Patches the working directories of the workspaces.

    :param terraform_domain: The domain corresponding to the targeted Terraform installation (either
                             Terraform Cloud or Enterprise).
    :param organization: The organization containing the workspaces to patch.
    :param workspaces: The workspaces to patch.
    :param new_working_directory: The new working directory to assign to the workspaces.
    :param no_tls: Whether to use SSL/TLS encryption when communicating with the Terraform API.
    :param write_output: Whether to print a tabulated result of the patch operations to STDOUT.
    :return: Whether all patch operations were successful. If even a single one failed, returns
             False.
    """

    json = {
        "data": {
            "type": "workspaces",
            "attributes": {
                "working-directory": "" if new_working_directory is None else new_working_directory
            }
        }
    }
    report = []

    def coalesce(working_directory: Optional[str]) -> str:
        if working_directory is None or len(working_directory) == 0:
            return "<none>"
        else:
            return working_directory

    def on_success(workspace: Workspace) -> None:
        report.append([
            workspace.name,
            coalesce(workspace.working_directory),
            coalesce(new_working_directory),
            "success",
            "none"
        ])

    def on_failure(workspace: Workspace, response: Union[Response, ErrorResponse]) -> None:
        report.append([
            workspace.name,
            coalesce(workspace.working_directory),
            coalesce(workspace.working_directory),
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
        write_output=write_output
    )

    if write_output:
        print((
            f'Terraform workspace working directory patch results for organization '
            f'"{organization}" at "{terraform_domain}":'
        ))
        print()
        print(
            tabulate(
                sorted(report, key=lambda x: (x[3], x[0])),
                headers=[
                    "Workspace",
                    "Working Directory Before",
                    "Working Directory After",
                    "Status",
                    "Message"
                ]
            )
        )
        print()

    return result
