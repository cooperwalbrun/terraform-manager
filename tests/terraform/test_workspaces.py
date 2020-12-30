import os
import sys
from unittest.mock import MagicMock, call

import responses
from pytest_mock import MockerFixture
from tabulate import tabulate
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform import TARGETING_SPECIFIC_WORKSPACES_TEXT
from terraform_manager.terraform.workspaces import fetch_all, batch_operation, _map_workspaces, \
    write_summary

from tests.utilities.tooling import test_workspace, TEST_API_URL, TEST_TERRAFORM_DOMAIN, \
    TEST_ORGANIZATION

_test_organization: str = "test"
_test_api_url: str = f"{TEST_API_URL}/organizations/{_test_organization}/workspaces"

_test_workspace1: Workspace = test_workspace(version="0.13.5")
_test_workspace2: Workspace = test_workspace(
    version="0.12.28", working_directory="test", agent_pool_id="test"
)

# yapf: disable
_test_json = {
    "data": [{
        "id": _test_workspace1.workspace_id,
        "attributes": {
            "auto-apply": _test_workspace1.auto_apply,
            "name": _test_workspace1.name,
            "terraform-version": _test_workspace1.terraform_version,
            "locked": _test_workspace1.is_locked,
            "working-directory": _test_workspace1.working_directory,
            "execution-mode": _test_workspace1.execution_mode,
            "speculative-enabled": _test_workspace1.speculative
        }
    }, {
        "id": _test_workspace2.workspace_id,
        "attributes": {
            "auto-apply": _test_workspace2.auto_apply,
            "name": _test_workspace2.name,
            "terraform-version": _test_workspace2.terraform_version,
            "locked": _test_workspace2.is_locked,
            "working-directory": _test_workspace2.working_directory,
            "execution-mode": _test_workspace2.execution_mode,
            "speculative-enabled": _test_workspace2.speculative
        }
    }]
}
# yapf: enable


def _establish_mocks(mocker: MockerFixture) -> None:
    mocker.patch("terraform_manager.terraform.credentials.find_token", return_value="test")


def test_map_workspaces() -> None:
    bad_tests = [[{"test": "test"}], [{"id": "good"}], [{"id": "good", "attributes": {}}]]
    for test in bad_tests:
        assert _map_workspaces(test) == []


@responses.activate
def test_fetch_all_workspaces(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=_test_json,
        status=200
    )
    assert fetch_all(TEST_TERRAFORM_DOMAIN,
                     _test_organization) == [_test_workspace1, _test_workspace2]


@responses.activate
def test_fetch_all_workspaces_with_filter(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=_test_json,
        status=200
    )
    assert fetch_all(
        TEST_TERRAFORM_DOMAIN,
        _test_organization,
        workspace_names=[_test_workspace2.name],
        blacklist=False
    ) == [_test_workspace2]


@responses.activate
def test_fetch_all_workspaces_with_wildcard_filter(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=_test_json,
        status=200
    )
    assert fetch_all(
        TEST_TERRAFORM_DOMAIN, _test_organization, workspace_names=["*"], blacklist=False
    ) == [_test_workspace1, _test_workspace2]


@responses.activate
def test_fetch_all_workspaces_with_inverted_filter(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=_test_json,
        status=200
    )
    assert fetch_all(
        TEST_TERRAFORM_DOMAIN,
        _test_organization,
        workspace_names=[_test_workspace2.name],
        blacklist=True
    ) == [_test_workspace1]


@responses.activate
def test_fetch_all_workspaces_with_inverted_wildcard_filter(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=_test_json,
        status=200
    )
    assert fetch_all(
        TEST_TERRAFORM_DOMAIN, _test_organization, workspace_names=["*"], blacklist=True
    ) == []


@responses.activate
def test_fetch_all_workspaces_bad_json_response(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    for test in [{}, {"data": {"bad json": "test"}}]:
        responses.add(
            responses.GET,
            f"{_test_api_url}?page[size]=100&page[number]=1",
            match_querystring=True,
            json=test,
            status=200
        )
        assert fetch_all(TEST_TERRAFORM_DOMAIN, _test_organization) == []


@responses.activate
def test_batch_operation(mocker: MockerFixture) -> None:
    for write_output in [True, False]:
        _establish_mocks(mocker)
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

        (field1, value1) = ("test-field1", _test_workspace1.terraform_version)
        (field2, value2) = ("test-field2", "test2")
        assert not batch_operation(
            TEST_TERRAFORM_DOMAIN,
            TEST_ORGANIZATION, [_test_workspace1, _test_workspace2],
            field_mappers=[lambda w: w.terraform_version, lambda w: w.name],
            field_names=[field1, field2],
            new_values=[value1, value2],
            report_only_value_mappers=[lambda x: "test-" + x, lambda x: "test-" + x],
            write_output=write_output
        )

        if write_output:
            # yapf: disable
            print_mock.assert_has_calls([
                call((
                    f'Terraform workspace {"/".join([field1, field2])} patch results for '
                    f'organization "{TEST_ORGANIZATION}" at "{TEST_TERRAFORM_DOMAIN}":'
                )),
                call(),
                call(
                    tabulate(
                        [
                            [
                                _test_workspace2.name,
                                field1,
                                "test-" + _test_workspace2.terraform_version,
                                "test-" + _test_workspace2.terraform_version,
                                "error",
                                str(error_json)
                            ],
                            [
                                _test_workspace2.name,
                                field2,
                                "test-" + _test_workspace2.name,
                                "test-" + _test_workspace2.name,
                                "error",
                                str(error_json)
                            ],
                            [
                                _test_workspace1.name,
                                field1,
                                "test-" + _test_workspace1.terraform_version,
                                "test-" + value1,
                                "success",
                                "value unchanged"
                            ],
                            [
                                _test_workspace1.name,
                                field2,
                                "test-" + _test_workspace1.name,
                                "test-" + value2,
                                "success",
                                "none"
                            ]
                        ],
                        headers=["Workspace", "Field", "Before", "After", "Status", "Message"]
                    )
                ),
                call()
            ])
            # yapf: enable
            assert print_mock.call_count == 4
        else:
            print_mock.assert_not_called()


def test_batch_operation_bad_arguments(mocker: MockerFixture) -> None:
    def name(workspace: Workspace) -> str:
        return workspace.name

    def test1() -> None:
        assert not batch_operation(
            TEST_TERRAFORM_DOMAIN,
            TEST_ORGANIZATION, [_test_workspace1, _test_workspace2],
            field_mappers=[name],
            field_names=["test", "test"],
            new_values=["test", "test"],
            write_output=write_output
        )

    def test2() -> None:
        assert not batch_operation(
            TEST_TERRAFORM_DOMAIN,
            TEST_ORGANIZATION, [_test_workspace1, _test_workspace2],
            field_mappers=[name, name],
            field_names=["test"],
            new_values=["test", "test"],
            write_output=write_output
        )

    def test3() -> None:
        assert not batch_operation(
            TEST_TERRAFORM_DOMAIN,
            TEST_ORGANIZATION, [_test_workspace1, _test_workspace2],
            field_mappers=[name, name],
            field_names=["test", "test"],
            new_values=["test"],
            write_output=write_output
        )

    def test4() -> None:
        assert not batch_operation(
            TEST_TERRAFORM_DOMAIN,
            TEST_ORGANIZATION, [_test_workspace1, _test_workspace2],
            field_mappers=[name, name],
            field_names=["test", "test"],
            new_values=["test", "test"],
            report_only_value_mappers=[str],
            write_output=write_output
        )

    def test5() -> None:
        assert not batch_operation(
            TEST_TERRAFORM_DOMAIN,
            TEST_ORGANIZATION, [_test_workspace1, _test_workspace2],
            field_mappers=[],
            field_names=["test"],
            new_values=["test"],
            write_output=write_output
        )

    for write_output in [True, False]:
        for test in [test1, test2, test3, test4, test5]:
            print_mock: MagicMock = mocker.patch("builtins.print")

            test()

            if write_output:
                # yapf: disable
                print_mock.assert_called_once_with((
                    "Error: invalid arguments passed to batch_operation. Ensure the number of "
                    "elements specified for field_mappers, field_names, new_values, and "
                    "report_only_value_mappers (if specified) match up."
                ), file=sys.stderr)
                # yapf: enable
            else:
                print_mock.assert_not_called()


def test_summary(mocker: MockerFixture) -> None:
    for write_output in [True, False]:
        print_mock: MagicMock = mocker.patch("builtins.print")
        workspaces = [_test_workspace1, _test_workspace2]
        write_summary(
            TEST_TERRAFORM_DOMAIN,
            TEST_ORGANIZATION,
            workspaces,
            targeting_specific_workspaces=True,
            write_output=write_output
        )
        # yapf: disable
        data = [
            [
                _test_workspace1.name,
                _test_workspace1.terraform_version,
                _test_workspace1.is_locked,
                _test_workspace1.auto_apply,
                _test_workspace1.speculative,
                "<none>",
                "<none>",
                _test_workspace1.execution_mode
            ], [
                _test_workspace2.name,
                _test_workspace2.terraform_version,
                _test_workspace2.is_locked,
                _test_workspace2.auto_apply,
                _test_workspace2.speculative,
                _test_workspace2.working_directory,
                _test_workspace2.agent_pool_id,
                _test_workspace2.execution_mode
            ]
        ]
        # yapf: enable
        if write_output:
            print_mock.assert_has_calls([
                call((
                    f'Terraform workspace summary for organization "{TEST_ORGANIZATION}" at '
                    f'"{TEST_TERRAFORM_DOMAIN}":'
                )),
                call(),
                call(
                    tabulate(
                        sorted(data, key=lambda x: x[0]),
                        headers=[
                            "Name",
                            "Version",
                            "Locked",
                            "Auto-Apply",
                            "Speculative",
                            "Working Directory",
                            "Agent Pool ID",
                            "Execution Mode"
                        ]
                    )
                ),
                call(),
                call(os.linesep + TARGETING_SPECIFIC_WORKSPACES_TEXT),
                call()
            ])
        else:
            print_mock.assert_not_called()
