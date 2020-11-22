from typing import List

import requests
from tabulate import tabulate
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform import get_api_headers
from terraform_manager.utilities.throttle import throttle
from terraform_manager.utilities.utilities import safe_http_request


def lock_or_unlock_workspaces(
    terraform_domain: str,
    workspaces: List[Workspace],
    *,
    set_lock: bool,
    write_output: bool = False
) -> bool:
    """
    Locks or unlocks each of the given workspaces.

    :param terraform_domain: The domain corresponding to the targeted Terraform installation (either
                             Terraform Cloud or Enterprise).
    :param workspaces: The workspaces to lock or unlock.
    :param set_lock: The desired state of the workspaces' locks. If True, workspaces will be locked.
                     If False, workspaces will be unlocked.
    :param write_output: Whether to print a tabulated result of the patch operations to STDOUT.
    :return: Whether all lock/unlock operations were successful. If even a single one failed,
             returns False.
    """

    headers = get_api_headers(terraform_domain, write_error_messages=write_output)
    operation = "lock" if set_lock else "unlock"
    base_url = f"https://{terraform_domain}/api/v2"
    report = []
    all_successful = True
    for workspace in workspaces:
        url = f"{base_url}/workspaces/{workspace.workspace_id}/actions/{operation}"
        response = safe_http_request(lambda: throttle(lambda: requests.post(url, headers=headers)))
        if response.status_code == 200 or response.status_code == 409:
            report.append([workspace.name, workspace.is_locked, set_lock, "success", "none"])
        else:
            all_successful = False
            report.append([
                workspace.name, workspace.is_locked, workspace.is_locked, "error", response.json()
            ])

    if write_output:
        print(
            tabulate(
                sorted(report, key=lambda x: (x[3], x[0])),
                headers=["Workspace", "Lock State Before", "Lock State After", "Status", "Message"]
            )
        )

    return all_successful
