import json
import sys
from typing import Dict, List, Any
from unittest.mock import MagicMock, call

import responses
from pytest_mock import MockerFixture
from tabulate import tabulate
from terraform_manager.entities.variable import Variable
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform.variables import create_variables_template, parse_variables, \
    _get_existing_variables, _update_variables, _create_variables, configure_variables

from tests.utilities.tooling import test_workspace, TEST_API_URL, TEST_TERRAFORM_DOMAIN, \
    TEST_ORGANIZATION

_variable_json: Dict[str, str] = {"key": "key1", "value": "value1"}

_test_workspace: Workspace = test_workspace()

_test_variable_id: str = "test1"
_test_variable: Variable = Variable(key="key", value="value")
_test_variable_api_json: Dict[str, List[Dict[str, Any]]] = {
    "data": [{
        "id": _test_variable_id, "type": "vars", "attributes": _test_variable.to_json()
    }]
}
_test_variables_with_ids: Dict[str, Variable] = {_test_variable_id: _test_variable}

_test_variables_api_url: str = f"{TEST_API_URL}/workspaces/{_test_workspace.workspace_id}/vars"
_test_patch_variable_api_url: str = \
    f"{TEST_API_URL}/workspaces/{_test_workspace.workspace_id}/vars/{_test_variable_id}"


def test_create_variables_template(mocker: MockerFixture) -> None:
    for write in [True, False]:
        file_handle_mock: MagicMock = mocker.patch("builtins.open")
        print_mock: MagicMock = mocker.patch("builtins.print")
        expected_templated_variables = [
            Variable(key="key1", value="value1").to_json(),
            Variable(key="key2", value="value2").to_json()
        ]
        expected_template_contents = json.dumps(expected_templated_variables, indent=2)

        assert create_variables_template(write_output=write)
        file_handle_mock.assert_called_once_with("template.json", "w")
        file_handle_mock.return_value.__enter__().write\
            .assert_called_once_with(expected_template_contents)
        if write:
            print_mock.assert_called_once_with(f"Successfully created template.json.")
        else:
            print_mock.assert_not_called()


def test_create_variables_template_error(mocker: MockerFixture) -> None:
    for write in [True, False]:
        file_handle_mock: MagicMock = mocker.patch("builtins.open")
        file_handle_mock.side_effect = Exception("Mocking a raised error")
        print_mock: MagicMock = mocker.patch("builtins.print")

        assert not create_variables_template(write_output=write)
        file_handle_mock.assert_called_once_with("template.json", "w")
        file_handle_mock.return_value.__enter__().write.assert_not_called()
        if write:
            # yapf: disable
            print_mock.assert_called_once_with((
                f"Error: something went wrong while writing the template.json file. Ensure you "
                "have permission to write files in the current working directory."
            ), file=sys.stderr)
            # yapf: enable
        else:
            print_mock.assert_not_called()


def test_parse_variables(mocker: MockerFixture) -> None:
    os_path_mock: MagicMock = mocker.patch("os.path.exists", return_value=True)
    file_handle_mock: MagicMock = mocker.patch("builtins.open")
    json_load_mock: MagicMock = mocker.patch("json.load", return_value=[_variable_json])

    filename = "test.json"
    parsed_variables = parse_variables(filename)

    assert parsed_variables == [Variable(key="key1", value="value1")]
    os_path_mock.assert_called_once_with(filename)
    file_handle_mock.assert_called_once_with(filename, "r")
    json_load_mock.assert_called_once()


def test_parse_variables_bad_json(mocker: MockerFixture) -> None:
    for test in [{}, {"key": "only a key"}]:
        for write in [True, False]:
            os_path_mock: MagicMock = mocker.patch("os.path.exists", return_value=True)
            file_handle_mock: MagicMock = mocker.patch("builtins.open")
            json_load_mock: MagicMock = mocker.patch("json.load", return_value=[test])
            print_mock: MagicMock = mocker.patch("builtins.print")

            filename = "test.json"
            parsed_variables = parse_variables(filename, write_output=write)

            assert parsed_variables == []
            os_path_mock.assert_called_once_with(filename)
            file_handle_mock.assert_called_once_with(filename, "r")
            json_load_mock.assert_called_once()
            if write:
                # yapf: disable
                print_mock.assert_called_once_with((
                    f"Warning: a variable was not successfully parsed from {filename}. Its JSON "
                    f"is {json.dumps(test)}"
                ), file=sys.stderr)
                # yapf: enable
            else:
                print_mock.assert_not_called()


def test_parse_variables_json_error(mocker: MockerFixture) -> None:
    for write in [True, False]:
        os_path_mock: MagicMock = mocker.patch("os.path.exists", return_value=True)
        file_handle_mock: MagicMock = mocker.patch("builtins.open")
        json_load_mock: MagicMock = mocker.patch("json.load")
        json_load_mock.side_effect = Exception("Mocking a raised error")
        print_mock: MagicMock = mocker.patch("builtins.print")

        filename = "test.json"
        parsed_variables = parse_variables(filename, write_output=write)

        assert parsed_variables == []
        os_path_mock.assert_called_once_with(filename)
        file_handle_mock.assert_called_once_with(filename, "r")
        json_load_mock.assert_called_once()
        if write:
            print_mock.assert_called_once_with(
                f"Error: unable to read and/or parse the {filename} file into JSON.",
                file=sys.stderr
            )
        else:
            print_mock.assert_not_called()


def test_parse_variables_file_missing(mocker: MockerFixture) -> None:
    os_path_mock: MagicMock = mocker.patch("os.path.exists", return_value=False)
    file_handle_mock: MagicMock = mocker.patch("builtins.open")
    json_load_mock: MagicMock = mocker.patch("json.load")
    print_mock: MagicMock = mocker.patch("builtins.print")

    filename = "test.json"
    parsed_variables = parse_variables(filename, write_output=True)

    assert parsed_variables == []
    os_path_mock.assert_called_once_with(filename)
    file_handle_mock.assert_not_called()
    json_load_mock.assert_not_called()
    print_mock.assert_called_once_with(
        f"Error: unable to read and/or parse the {filename} file into JSON.", file=sys.stderr
    )


@responses.activate
def test_get_existing_variables() -> None:
    responses.add(responses.GET, _test_variables_api_url, json=_test_variable_api_json, status=200)
    existing_variables = _get_existing_variables(
        TEST_API_URL, headers={}, workspace=_test_workspace
    )
    assert existing_variables == _test_variables_with_ids


@responses.activate
def test_get_existing_variables_bad_json_response() -> None:
    for test in [{}, {"data": {}}, {"data": [{}]}, {"data": [{"id": "1", "attributes": {}}]}]:
        responses.add(responses.GET, _test_variables_api_url, json=test, status=200)
        existing_variables = _get_existing_variables(
            TEST_API_URL, headers={}, workspace=_test_workspace
        )
        assert existing_variables is None


@responses.activate
def test_get_existing_variables_api_error() -> None:
    responses.add(responses.GET, _test_variables_api_url, status=500)
    existing_variables = _get_existing_variables(
        TEST_API_URL, headers={}, workspace=_test_workspace
    )
    assert existing_variables is None


@responses.activate
def test_update_variables() -> None:
    success_mock: Any = MagicMock()
    error_mock: Any = MagicMock()
    responses.add(responses.PATCH, _test_patch_variable_api_url, status=200)

    assert _update_variables(
        TEST_API_URL,
        headers={},
        workspace=_test_workspace,
        updates=_test_variables_with_ids,
        on_success=success_mock,
        on_failure=error_mock
    )
    success_mock.assert_called_once()
    error_mock.assert_not_called()


@responses.activate
def test_update_variables_empty_dict() -> None:
    success_mock: Any = MagicMock()
    error_mock: Any = MagicMock()

    assert _update_variables(
        TEST_API_URL,
        headers={},
        workspace=_test_workspace,
        updates={},
        on_success=success_mock,
        on_failure=error_mock
    )
    success_mock.assert_not_called()
    error_mock.assert_not_called()


@responses.activate
def test_update_variables_api_error() -> None:
    success_mock: Any = MagicMock()
    error_mock: Any = MagicMock()
    responses.add(responses.PATCH, _test_patch_variable_api_url, status=500)

    assert not _update_variables(
        TEST_API_URL,
        headers={},
        workspace=_test_workspace,
        updates=_test_variables_with_ids,
        on_success=success_mock,
        on_failure=error_mock
    )
    success_mock.asser_not_called()
    error_mock.assert_called_once()


@responses.activate
def test_create_variables() -> None:
    success_mock: Any = MagicMock()
    error_mock: Any = MagicMock()
    responses.add(responses.POST, _test_variables_api_url, status=201)

    assert _create_variables(
        TEST_API_URL,
        headers={},
        workspace=_test_workspace,
        creations=[_test_variable],
        on_success=success_mock,
        on_failure=error_mock
    )
    success_mock.assert_called_once()
    error_mock.assert_not_called()


@responses.activate
def test_create_variables_empty_list() -> None:
    success_mock: Any = MagicMock()
    error_mock: Any = MagicMock()

    assert _create_variables(
        TEST_API_URL,
        headers={},
        workspace=_test_workspace,
        creations=[],
        on_success=success_mock,
        on_failure=error_mock
    )
    success_mock.assert_not_called()
    error_mock.assert_not_called()


@responses.activate
def test_create_variables_api_error() -> None:
    success_mock: Any = MagicMock()
    error_mock: Any = MagicMock()
    responses.add(responses.POST, _test_variables_api_url, status=500)

    assert not _create_variables(
        TEST_API_URL,
        headers={},
        workspace=_test_workspace,
        creations=[_test_variable],
        on_success=success_mock,
        on_failure=error_mock
    )
    success_mock.assert_not_called()
    error_mock.assert_called_once()


def test_configure_variables(mocker: MockerFixture) -> None:
    tests = [(True, True), (False, True), (True, False), (False, False)]
    for create_return_value, update_return_value in tests:
        for existing_variables in [None, {}, _test_variables_with_ids]:
            fetch_mock: MagicMock = mocker.patch(
                "terraform_manager.terraform.variables._get_existing_variables",
                return_value=existing_variables
            )
            create_mock: MagicMock = mocker.patch(
                "terraform_manager.terraform.variables._create_variables",
                return_value=create_return_value
            )
            update_mock: MagicMock = mocker.patch(
                "terraform_manager.terraform.variables._update_variables",
                return_value=update_return_value
            )

            result = configure_variables(
                TEST_TERRAFORM_DOMAIN,
                TEST_ORGANIZATION,
                workspaces=[_test_workspace],
                variables=[_test_variable]
            )
            if existing_variables is None:
                assert result is False
                fetch_mock.assert_called_once()
                create_mock.assert_not_called()
                update_mock.assert_not_called()
            else:
                assert result == (create_return_value and update_return_value)
                fetch_mock.assert_called_once()
                create_mock.assert_called_once()
                update_mock.assert_called_once()


@responses.activate
def test_configure_variables_report(mocker: MockerFixture) -> None:
    tests = {"create": {}, "update": _test_variables_with_ids}
    for operation, existing_variables in tests.items():
        mocker.patch(
            "terraform_manager.terraform.variables._get_existing_variables",
            return_value=existing_variables
        )
        responses.add(responses.POST, _test_variables_api_url, status=201)
        responses.add(responses.PATCH, _test_patch_variable_api_url, status=200)
        print_mock: MagicMock = mocker.patch("builtins.print")

        configure_variables(
            TEST_TERRAFORM_DOMAIN,
            TEST_ORGANIZATION,
            workspaces=[_test_workspace],
            variables=[_test_variable],
            write_output=True
        )

        table_data = [[_test_workspace.name, _test_variable.key, operation, "success", ""]]
        print_mock.assert_has_calls([
            call((
                f'Terraform workspace variable configuration results for organization '
                f'"{TEST_ORGANIZATION}" at "{TEST_TERRAFORM_DOMAIN}":'
            )),
            call(),
            call(
                tabulate(
                    sorted(table_data, key=lambda x: (x[3], x[2], x[0], x[1])),
                    headers=["Workspace", "Variable", "Operation", "Status", "Message"]
                )
            ),
            call()
        ])
