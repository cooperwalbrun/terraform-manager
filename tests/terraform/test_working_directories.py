from typing import Optional
from unittest.mock import MagicMock, call

import responses
from pytest_mock import MockerFixture
from tabulate import tabulate
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform.working_directories import patch_working_directories

from tests.utilities.tooling import TEST_API_URL, test_workspace, TEST_ORGANIZATION, \
    TEST_TERRAFORM_DOMAIN

_test_workspace1: Workspace = test_workspace(working_directory="")
_test_workspace2: Workspace = test_workspace(working_directory="stage")


def _coalesce(working_directory: Optional[str]) -> str:
    if working_directory is None or len(working_directory) == 0:
        return "<none>"
    else:
        return working_directory


@responses.activate
def test_patch_versions(mocker: MockerFixture) -> None:
    for test in [None, "test"]:
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
        assert not patch_working_directories(
            TEST_TERRAFORM_DOMAIN,
            TEST_ORGANIZATION, [_test_workspace1, _test_workspace2],
            new_working_directory=test,
            write_output=True
        )
        # yapf: disable
        print_mock.assert_has_calls([
            call((
                f'Terraform workspace working directory patch results for organization '
                f'"{TEST_ORGANIZATION}" at "{TEST_TERRAFORM_DOMAIN}":'
            )),
            call(),
            call(
                tabulate(
                    [
                        [
                            _test_workspace2.name,
                            _test_workspace2.working_directory,
                            _test_workspace2.working_directory,
                            "error",
                            str(error_json)
                        ],
                        [
                            _test_workspace1.name,
                            _coalesce(_test_workspace1.working_directory),
                            _coalesce(test),
                            "success",
                            "none"
                            if _coalesce(test) != _coalesce(_test_workspace1.working_directory)
                            else "working directory unchanged"
                        ]
                    ],
                    headers=[
                        "Workspace",
                        "Working Directory Before",
                        "Working Directory After",
                        "Status",
                        "Message"
                    ]
                )

            ),
            call()
        ])
        # yapf: enable
        assert print_mock.call_count == 4
