from unittest.mock import MagicMock

import responses
from pytest_mock import MockerFixture
from terraform_manager.entities.run import Run
from terraform_manager.terraform.runs import _get_active_runs_for_workspace, launch_run_watcher

from tests.utilities.tooling import TEST_API_URL, test_run, TEST_TERRAFORM_DOMAIN, \
    establish_asciimatics_widget_mocks

_test_run: Run = test_run(has_changes=True)
_test_api_url: str = (
    f"{TEST_API_URL}/workspaces/{_test_run.workspace.workspace_id}"
    f"/runs?page[size]=100&page[number]=1"
)
_test_json = {
    "data": [{
        "id": _test_run.run_id,
        "attributes": {
            "created-at": _test_run.created_at,
            "status": _test_run.status,
            "status-timestamps": _test_run.all_status_timestamps,
            "has-changes": _test_run.has_changes
        }
    }]
}


def _establish_mocks(mocker: MockerFixture) -> None:
    mocker.patch("terraform_manager.terraform.credentials.find_token", return_value="test")


@responses.activate
def test_get_active_runs_for_workspace(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    print_mock: MagicMock = mocker.patch("builtins.print")
    responses.add(responses.GET, _test_api_url, match_querystring=True, json=_test_json, status=200)

    assert _get_active_runs_for_workspace(
        TEST_TERRAFORM_DOMAIN, _test_run.workspace, no_tls=False, token=None
    ) == [_test_run]
    print_mock.assert_not_called()  # --watch-runs does not tolerate writing to STDOUT


@responses.activate
def test_get_active_runs_for_workspace_bad_json(mocker: MockerFixture) -> None:
    # yapf: disable
    tests = [
        {},
        {"data": {}},
        {"data": []},
        {"data": [{"attributes": {}}]},
        {"data": [{"id": _test_run.run_id}]},
        {"data": [{"id": _test_run.run_id, "attributes": {}}]}
    ]
    # yapf: enable
    for test in tests:
        _establish_mocks(mocker)
        print_mock: MagicMock = mocker.patch("builtins.print")
        responses.add(responses.GET, _test_api_url, match_querystring=True, json=test, status=200)

        assert _get_active_runs_for_workspace(
            TEST_TERRAFORM_DOMAIN, _test_run.workspace, no_tls=False, token=None
        ) == []
        print_mock.assert_not_called()  # --watch-runs does not tolerate writing to STDOUT


@responses.activate
def test_get_active_runs_for_workspace_error_response(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    print_mock: MagicMock = mocker.patch("builtins.print")
    responses.add(responses.GET, _test_api_url, match_querystring=True, json={}, status=500)

    assert _get_active_runs_for_workspace(
        TEST_TERRAFORM_DOMAIN, _test_run.workspace, no_tls=False, token=None
    ) == []
    print_mock.assert_not_called()  # --watch-runs does not tolerate writing to STDOUT


def test_launch_watcher(mocker: MockerFixture) -> None:
    for write_output in [True, False]:
        establish_asciimatics_widget_mocks(mocker)
        print_mock: MagicMock = mocker.patch("builtins.print")
        mocker.patch(
            "terraform_manager.terraform.runs._get_active_runs_for_workspace",
            return_value=[_test_run]
        )
        loop_mock: MagicMock = mocker.patch(
            "terraform_manager.interface.run_watcher.screen_player.run_watcher_loop",
            return_value=None
        )

        launch_run_watcher(
            TEST_TERRAFORM_DOMAIN, [_test_run.workspace],
            targeting_specific_workspaces=False,
            no_tls=False,
            token=None,
            write_output=write_output
        )

        if write_output:
            print_mock.assert_not_called()  # --watch-runs does not tolerate writing to STDOUT
            loop_mock.assert_called_once()
        else:
            print_mock.assert_not_called()  # --watch-runs does not tolerate writing to STDOUT
            loop_mock.assert_not_called()
