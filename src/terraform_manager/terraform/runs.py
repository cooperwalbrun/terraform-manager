import sys
from typing import Optional, List

import requests
from asciimatics.exceptions import ResizeScreenError
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from terraform_manager.entities.run import Run
from terraform_manager.entities.workspace import Workspace
from terraform_manager.interface.run_watcher.active_runs_view import ActiveRunsView
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
    active_runs = []

    headers = get_api_headers(terraform_domain, token=token, write_error_messages=False)
    base_url = f"{get_protocol(no_tls)}://{terraform_domain}/api/v2"
    endpoint = f"{base_url}/workspaces/{workspace.workspace_id}/runs"
    parameters = {
        # See: https://www.terraform.io/docs/cloud/api/index.html#pagination
        # Note that this method only checks the most recent 100 runs for the workspace (this will
        # always be sufficient in practice)
        "page[number]": 1,
        "page[size]": 100
    }
    response = safe_http_request(
        lambda: throttle(lambda: requests.get(endpoint, headers=headers, params=parameters))
    )

    if response.status_code == 200 and len(response.json().get("data")) > 0:
        for run_json in response.json()["data"]:
            if "attributes" in run_json:
                attributes = run_json["attributes"]
                if "status" in attributes and "status-timestamps" in attributes:
                    run = Run(
                        workspace=workspace,
                        status=attributes["status"],
                        all_status_timestamps=attributes["status-timestamps"]
                    )
                    if run.is_active:
                        active_runs.append(run)
    return active_runs


def launch_run_watcher(
    terraform_domain: str,
    organization: str,
    workspaces: List[Workspace],
    *,
    targeting_specific_workspaces: bool,
    no_tls: bool = False,
    token: Optional[str] = None,
    write_output: bool = False
) -> None:
    """
    Launches a TUI for near-real-time report of all workspace run activity within the organization.
    By design, this method will not terminate until the program is killed by the user (e.g. via
    Ctrl+C).

    :param terraform_domain: The domain corresponding to the targeted Terraform installation (either
                             Terraform Cloud or Enterprise).
    :param organization: The organization containing the workspaces to lock/unlock.
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

    def screen_player(screen: Screen) -> None:
        screen.clear()
        active_runs_frame = ActiveRunsView(
            screen,
            organization,
            run_generator=get_all_runs,
            targeting_specific_workspaces=targeting_specific_workspaces
        )
        # Setting the duration to 10 will force asciimatic to re-render the scene twice per second
        # (there are about 20 frames per second), but the API calls will NOT happen that frequently;
        # see ActiveRunsView for more information
        scenes = [Scene([active_runs_frame], duration=10, clear=False, name="main")]
        screen.play(scenes, stop_on_resize=True, repeat=True)

    if write_output:
        while True:
            try:
                Screen.wrapper(screen_player)
            except ResizeScreenError:
                # We simply need to re-run Screen.wrapper() when this happens, which will happen
                # automatically during the next iteration of this infinite loop
                continue
            except KeyboardInterrupt:  # This is thrown when the program is interrupted by the user
                sys.exit(0)
