import textwrap
from typing import List, Optional

import requests
from tabulate import tabulate
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform import get_api_headers, MESSAGE_COLUMN_CHARACTER_COUNT
from terraform_manager.utilities.throttle import throttle
from terraform_manager.utilities.utilities import safe_http_request, get_protocol, wrap_text


def lock_or_unlock_workspaces(
    terraform_domain: str,
    organization: str,
    workspaces: List[Workspace],
    *,
    set_lock: bool,
    no_tls: bool = False,
    token: Optional[str] = None,
    write_output: bool = False
) -> bool:
    """
    Locks or unlocks each of the given workspaces.

    :param terraform_domain: The domain corresponding to the targeted Terraform installation (either
                             Terraform Cloud or Enterprise).
    :param organization: The organization containing the workspaces to lock/unlock.
    :param workspaces: The workspaces to lock or unlock.
    :param set_lock: The desired state of the workspaces' locks. If True, workspaces will be locked.
                     If False, workspaces will be unlocked.
    :param no_tls: Whether to use SSL/TLS encryption when communicating with the Terraform API.
    :param token: A token suitable for authenticating against the Terraform API. If not specified, a
                  token will be searched for in the documented locations.
    :param write_output: Whether to print a tabulated result of the patch operations to STDOUT.
    :return: Whether all lock/unlock operations were successful. If even a single one failed,
             returns False.
    """

    headers = get_api_headers(terraform_domain, token=token, write_error_messages=write_output)
    operation = "lock" if set_lock else "unlock"
    base_url = f"{get_protocol(no_tls)}://{terraform_domain}/api/v2"
    report = []
    all_successful = True
    for workspace in workspaces:
        url = f"{base_url}/workspaces/{workspace.workspace_id}/actions/{operation}"
        response = safe_http_request(lambda: throttle(lambda: requests.post(url, headers=headers)))
        if response.status_code == 200:
            report.append([workspace.name, workspace.is_locked, set_lock, "success", "none"])
        elif response.status_code == 409:
            report.append([
                workspace.name,
                workspace.is_locked,
                set_lock,
                "success",
                f"workspace was already {operation}ed"
            ])
        else:
            all_successful = False
            report.append([
                workspace.name,
                workspace.is_locked,
                workspace.is_locked,
                "error",
                wrap_text(str(response.json()), MESSAGE_COLUMN_CHARACTER_COUNT)
            ])

    if write_output:
        print((
            f'Terraform workspace {operation} results for organization "{organization}" at '
            f'"{terraform_domain}":'
        ))
        print()
        print(
            tabulate(
                sorted(report, key=lambda x: (x[3], x[0])),
                headers=["Workspace", "Lock State Before", "Lock State After", "Status", "Message"]
            )
        )
        print()

    return all_successful
