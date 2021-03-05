from typing import Optional, List

import requests
from terraform_manager.entities.run import Run
from terraform_manager.entities.workspace import Workspace
from terraform_manager.interface.run_watcher import screen_player
from terraform_manager.interface.run_watcher.active_runs_view_shared_state import \
    ActiveRunsViewSharedState
from terraform_manager.terraform import get_api_headers
from terraform_manager.utilities.throttle import throttle
from terraform_manager.utilities.utilities import get_protocol, safe_http_request


def _get_active_runs_for_workspace(
    terraform_domain: str,
    workspace: Workspace,
    *,
    no_tls: bool = False,
    token: Optional[str] = None
) -> List[Run]:
    required_attributes = ["created-at", "status", "status-timestamps", "has-changes"]
    active_runs = []

    headers = get_api_headers(terraform_domain, token=token, write_error_messages=False)
    base_url = f"{get_protocol(no_tls)}://{terraform_domain}/api/v2"
    endpoint = f"{base_url}/workspaces/{workspace.workspace_id}/runs"
    parameters = {
        # See: https://www.terraform.io/docs/cloud/api/index.html#pagination
        # Note that this method only checks the most recent 100 runs for the workspace (this will be
        # sufficient in practice)
        "page[number]": 1,
        "page[size]": 100
    }
    response = safe_http_request(
        lambda: throttle(lambda: requests.get(endpoint, headers=headers, params=parameters))
    )

    if response.status_code == 200:
        json = response.json()
        if "data" in json and len(json["data"]) > 0:
            for run_json in json["data"]:
                if "id" in run_json and "attributes" in run_json:
                    attributes = run_json["attributes"]
                    if all([x in attributes for x in required_attributes]):
                        run = Run(
                            run_id=run_json["id"],
                            workspace=workspace,
                            created_at=attributes["created-at"],
                            status=attributes["status"],
                            all_status_timestamps=attributes["status-timestamps"],
                            has_changes=attributes["has-changes"]
                        )
                        if run.is_active and run.has_changes:
                            active_runs.append(run)
    return active_runs


def launch_run_watcher(
    terraform_domain: str,
    workspaces: List[Workspace],
    *,
    targeting_specific_workspaces: bool,
    no_tls: bool = False,
    token: Optional[str] = None,
    write_output: bool = False
) -> None:
    """
    Launches a TUI for near-real-time reporting of all workspace run activity within the
    organization. By design, this method will not terminate until the program is killed by the user
    (e.g. via Ctrl+C).

    :param terraform_domain: The domain corresponding to the targeted Terraform installation (either
                             Terraform Cloud or Enterprise).
    :param workspaces: The workspaces to lock or unlock.
    :param targeting_specific_workspaces: Whether one or more workspaces was specified in order to
                                          filter the list of workspaces when they were fetched.
    :param no_tls: Whether to use SSL/TLS encryption when communicating with the Terraform API.
    :param token: A token suitable for authenticating against the Terraform API. If not specified, a
                  token will be searched for in the documented locations.
    :param write_output: Whether to print the report to STDOUT. If this is False, this method is a
                         no-op.
    :return: None.
    """
    def get_all_runs() -> List[Run]:
        report = []
        for workspace in workspaces:
            report.extend(
                _get_active_runs_for_workspace(
                    terraform_domain, workspace, no_tls=no_tls, token=token
                )
            )
        return report

    if write_output:
        state = ActiveRunsViewSharedState(
            run_generator=get_all_runs, targeting_specific_workspaces=targeting_specific_workspaces
        )
        screen_player.run_watcher_loop(state)
