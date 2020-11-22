from unittest.mock import MagicMock, call

import responses
from pytest_mock import MockerFixture
from tabulate import tabulate
from terraform_manager.terraform.locking import lock_or_unlock_workspaces

from tests.utilities.tooling import test_workspace, TEST_API_URL, TEST_TERRAFORM_DOMAIN, \
    establish_credential_mocks


@responses.activate
def test_lock_or_unlock_workspaces(mocker: MockerFixture) -> None:
    establish_credential_mocks(mocker)
    print_mock: MagicMock = mocker.patch("builtins.print")
    for test in [True, False]:
        for status in [200, 409]:  # The POST returns 409 if a workspace is already locked/unlocked
            operation = "lock" if test else "unlock"
            _test_workspace1 = test_workspace(locked=not test)
            _test_workspace2 = test_workspace(locked=True)
            error_json = {"data": {"id": _test_workspace2.workspace_id}}
            responses.add(
                responses.POST,
                f"{TEST_API_URL}/workspaces/{_test_workspace1.workspace_id}/actions/{operation}",
                status=status
            )
            responses.add(
                responses.POST,
                f"{TEST_API_URL}/workspaces/{_test_workspace2.workspace_id}/actions/{operation}",
                json=error_json,
                status=500
            )
            assert not lock_or_unlock_workspaces(
                TEST_TERRAFORM_DOMAIN, [_test_workspace1, _test_workspace2],
                set_lock=test,
                write_output=True
            )
            # yapf: disable
            print_mock.assert_has_calls([
                call(
                    tabulate(
                        [
                            [
                                _test_workspace2.name,
                                _test_workspace2.is_locked,
                                _test_workspace2.is_locked,
                                "error",
                                str(error_json)
                            ],
                            [
                                _test_workspace1.name,
                                _test_workspace1.is_locked,
                                test,
                                "success",
                                "none"
                            ]
                        ],
                        headers=[
                            "Workspace",
                            "Lock State Before",
                            "Lock State After",
                            "Status",
                            "Message"
                        ])

                )
            ])
            # yapf: enable
