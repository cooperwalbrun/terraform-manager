from unittest.mock import MagicMock, call

import responses
from pytest_mock import MockerFixture
from tabulate import tabulate
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform.working_directories import patch_working_directories

from tests.utilities.tooling import establish_credential_mocks, TEST_API_URL, test_workspace, \
    TEST_ORGANIZATION, TEST_TERRAFORM_DOMAIN

_test_workspace1: Workspace = test_workspace(working_directory="")
_test_workspace2: Workspace = test_workspace(working_directory="stage")


@responses.activate
def test_patch_versions(mocker: MockerFixture) -> None:
    establish_credential_mocks(mocker)
    print_mock: MagicMock = mocker.patch("builtins.print")
    test_working_directory = "test"
    error_json = {"data": {"id": _test_workspace2.workspace_id}}
    responses.add(
        responses.PATCH, f"{TEST_API_URL}/workspaces/{_test_workspace1.workspace_id}", status=200
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
        new_working_directory=test_working_directory,
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
                        "<none>",
                        test_working_directory,
                        "success",
                        "none"
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
