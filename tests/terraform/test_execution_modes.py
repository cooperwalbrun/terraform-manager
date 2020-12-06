import sys
from unittest.mock import MagicMock, call

import responses
from pytest_mock import MockerFixture
from tabulate import tabulate
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform.execution_modes import patch_execution_modes

from tests.utilities.tooling import TEST_API_URL, test_workspace, TEST_ORGANIZATION, \
    TEST_TERRAFORM_DOMAIN

_test_workspace1: Workspace = test_workspace(execution_mode="remote")
_test_workspace2: Workspace = test_workspace(execution_mode="remote")


@responses.activate
def test_patch_execution_modes(mocker: MockerFixture) -> None:
    for test in ["remote", "local"]:
        mocker.patch("terraform_manager.terraform.credentials.find_token", return_value="test")
        print_mock: MagicMock = mocker.patch("builtins.print")
        error_json = {"data": {"id": _test_workspace2.workspace_id}}
        responses.add(
            responses.PATCH,
            f"{TEST_API_URL}/workspaces/{_test_workspace1.workspace_id}",
            status=200
        )
        responses.add(
            responses.PATCH,
            f"{TEST_API_URL}/workspaces/{_test_workspace2.workspace_id}",
            json=error_json,
            status=500
        )
        assert not patch_execution_modes(
            TEST_TERRAFORM_DOMAIN,
            TEST_ORGANIZATION, [_test_workspace1, _test_workspace2],
            new_execution_mode=test,
            write_output=True
        )
        # yapf: disable
        print_mock.assert_has_calls([
            call((
                f'Terraform workspace execution mode patch results for organization '
                f'"{TEST_ORGANIZATION}" at "{TEST_TERRAFORM_DOMAIN}":'
            )),
            call(),
            call(
                tabulate(
                    [
                        [
                            _test_workspace2.name,
                            _test_workspace2.execution_mode,
                            _test_workspace2.execution_mode,
                            "error",
                            str(error_json)
                        ],
                        [
                            _test_workspace1.name,
                            _test_workspace1.execution_mode,
                            test,
                            "success",
                            "none" if test != _test_workspace1.execution_mode
                            else "execution mode unchanged"
                        ]
                    ],
                    headers=[
                        "Workspace",
                        "Execution Mode Before",
                        "Execution Mode After",
                        "Status",
                        "Message"
                    ]
                )

            ),
            call()
        ])
        # yapf: enable
        assert print_mock.call_count == 4


def test_patch_execution_modes_invalid_mode(mocker: MockerFixture) -> None:
    batch_mock: MagicMock = mocker.patch(
        "terraform_manager.terraform.execution_modes.batch_operation"
    )
    print_mock: MagicMock = mocker.patch("builtins.print")
    test_mode = "something-invalid"
    assert not patch_execution_modes(
        TEST_TERRAFORM_DOMAIN,
        TEST_ORGANIZATION, [_test_workspace1, _test_workspace2],
        new_execution_mode=test_mode,
        write_output=True
    )
    batch_mock.assert_not_called()
    print_mock.assert_called_once_with(
        f"Error: invalid execution-mode specified: {test_mode}", file=sys.stderr
    )
