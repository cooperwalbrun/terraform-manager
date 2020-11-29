import sys
from typing import Dict, Any, List, Optional
from unittest.mock import MagicMock, call

from pytest_mock import MockerFixture
from terraform_manager.__main__ import main
from terraform_manager.entities.variable import Variable
from terraform_manager.entities.workspace import Workspace

from tests.utilities.tooling import test_workspace, TEST_ORGANIZATION

_test_workspace1: Workspace = test_workspace()
_test_workspace2: Workspace = test_workspace()

_bool_flags: Dict[str, bool] = {
    # Below, we mimic the argparse functionality for boolean flags by specifying a default value for
    # them
    "no_tls": False,
    "blacklist": False,
    "version_summary": False,
    "lock_workspaces": False,
    "unlock_workspaces": False,
    "clear_working_directory": False,
    "create_variables_template": False
}


def _arguments(merge_with: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    arguments = {"organization": TEST_ORGANIZATION}
    if merge_with is None:
        return {**arguments, **_bool_flags}
    else:
        return {**arguments, **_bool_flags, **merge_with}


def _mock_fetch_workspaces(mocker: MockerFixture, return_value: List[Workspace]) -> MagicMock:
    # We have to mock the fetch_all that the Terraform class imports and uses - in other words we
    # mock the call site usage, not the definition site usage
    return mocker.patch("terraform_manager.entities.terraform.fetch_all", return_value=return_value)


def _mock_arguments(mocker: MockerFixture, arguments: Dict[str, Any]) -> MagicMock:
    return mocker.patch("terraform_manager.__main__.parse_arguments", return_value=arguments)


def _error_message(text: str) -> call:
    return call(text, file=sys.stderr)


def test_no_arguments(mocker: MockerFixture) -> None:
    mocker.patch("terraform_manager.__main__.parse_arguments", return_value=_bool_flags)
    fail_mock: MagicMock = mocker.patch("terraform_manager.__main__.fail", return_value=None)
    main()
    fail_mock.assert_called_once()


def test_no_tls_against_terraform_cloud(mocker: MockerFixture) -> None:
    print_mock: MagicMock = mocker.patch("builtins.print")
    fail_mock: MagicMock = mocker.patch("terraform_manager.__main__.fail", return_value=None)
    _mock_fetch_workspaces(mocker, [])
    _mock_arguments(mocker, _arguments({"no_tls": True}))

    main()

    print_mock.assert_has_calls([
        _error_message(
            "Error: you should never disable SSL/TLS when interacting with Terraform Cloud."
        )
    ])
    fail_mock.assert_called_once()


def test_unexpected_blacklist_flag(mocker: MockerFixture) -> None:
    print_mock: MagicMock = mocker.patch("builtins.print")
    fail_mock: MagicMock = mocker.patch("terraform_manager.__main__.fail", return_value=None)
    _mock_fetch_workspaces(mocker, [])
    _mock_arguments(mocker, _arguments({"blacklist": True}))

    main()

    print_mock.assert_has_calls([
        _error_message((
            "Error: the blacklist flag is only applicable when you specify a workspace(s) to "
            "filter on."
        ))
    ])
    fail_mock.assert_called_once()


def test_no_workspaces_selected(mocker: MockerFixture) -> None:
    print_mock: MagicMock = mocker.patch("builtins.print")
    fail_mock: MagicMock = mocker.patch("terraform_manager.__main__.fail", return_value=None)
    _mock_fetch_workspaces(mocker, [])
    _mock_arguments(mocker, _arguments())

    main()

    print_mock.assert_has_calls([
        _error_message("Error: no workspaces could be found in your organization.")
    ])
    fail_mock.assert_called_once()


def test_no_workspaces_selected_with_filter(mocker: MockerFixture) -> None:
    print_mock: MagicMock = mocker.patch("builtins.print")
    fail_mock: MagicMock = mocker.patch("terraform_manager.__main__.fail", return_value=None)
    _mock_fetch_workspaces(mocker, [])
    _mock_arguments(
        mocker, _arguments({"workspaces": [_test_workspace1.name, _test_workspace2.name]})
    )

    main()

    print_mock.assert_has_calls([
        _error_message(
            "Error: no workspaces could be found with these name(s): {}, {}".format(
                _test_workspace1.name, _test_workspace2.name
            )
        )
    ])
    fail_mock.assert_called_once()


def test_version_summary(mocker: MockerFixture) -> None:
    fail_mock: MagicMock = mocker.patch("terraform_manager.__main__.fail", return_value=None)
    summary_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.Terraform.write_version_summary", return_value=None
    )
    _mock_fetch_workspaces(mocker, [_test_workspace1])
    _mock_arguments(mocker, _arguments({"version_summary": True}))

    main()

    summary_mock.assert_called_once()
    fail_mock.assert_not_called()


def test_patch_versions(mocker: MockerFixture) -> None:
    for success in [True, False]:
        fail_mock: MagicMock = mocker.patch("terraform_manager.__main__.fail", return_value=None)
        check_mock: MagicMock = mocker.patch(
            "terraform_manager.entities.terraform.Terraform.check_versions", return_value=True
        )
        patch_mock: MagicMock = mocker.patch(
            "terraform_manager.entities.terraform.Terraform.patch_versions", return_value=success
        )
        desired_version = "0.13.5"
        _mock_fetch_workspaces(mocker, [_test_workspace1])
        _mock_arguments(mocker, _arguments({"patch_versions": desired_version}))

        main()

        check_mock.assert_called_once_with(desired_version)
        patch_mock.assert_called_once_with(desired_version)
        if success:
            fail_mock.assert_not_called()
        else:
            fail_mock.assert_called_once()


def test_patch_versions_invalid_version(mocker: MockerFixture) -> None:
    print_mock: MagicMock = mocker.patch("builtins.print")
    fail_mock: MagicMock = mocker.patch("terraform_manager.__main__.fail", return_value=None)
    desired_version = "NOT-A-VALID-SEMANTIC-VERSION"
    _mock_fetch_workspaces(mocker, [_test_workspace1])
    _mock_arguments(mocker, _arguments({"patch_versions": desired_version}))

    main()

    print_mock.assert_has_calls([
        _error_message(
            f"Error: the value for patch_versions you specified ({desired_version}) is not valid."
        )
    ])
    fail_mock.assert_called_once()


def test_patch_versions_downgrade_version(mocker: MockerFixture) -> None:
    print_mock: MagicMock = mocker.patch("builtins.print")
    fail_mock: MagicMock = mocker.patch("terraform_manager.__main__.fail", return_value=None)
    check_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.Terraform.check_versions", return_value=False
    )
    _mock_fetch_workspaces(mocker, [_test_workspace1])
    # The version specified below does not actually matter for this test because we are forcing
    # False to return from check_versions with the mock above
    desired_version = "0.13.0"
    _mock_arguments(mocker, _arguments({"patch_versions": desired_version}))

    main()

    check_mock.assert_called_once_with(desired_version)
    print_mock.assert_has_calls([
        _error_message((
            "Error: at least one of the target workspaces has a version newer than the one you are "
            "attempting to change to. No workspaces were updated."
        ))
    ])
    fail_mock.assert_called_once()


def test_lock_workspaces(mocker: MockerFixture) -> None:
    for success in [True, False]:
        fail_mock: MagicMock = mocker.patch("terraform_manager.__main__.fail", return_value=None)
        lock_mock: MagicMock = mocker.patch(
            "terraform_manager.entities.terraform.Terraform.lock_workspaces", return_value=success
        )
        _mock_fetch_workspaces(mocker, [_test_workspace1])
        _mock_arguments(mocker, _arguments({"lock_workspaces": True}))

        main()

        lock_mock.assert_called_once()
        if success:
            fail_mock.assert_not_called()
        else:
            fail_mock.assert_called_once()


def test_unlock_workspaces(mocker: MockerFixture) -> None:
    for success in [True, False]:
        fail_mock: MagicMock = mocker.patch("terraform_manager.__main__.fail", return_value=None)
        unlock_mock: MagicMock = mocker.patch(
            "terraform_manager.entities.terraform.Terraform.unlock_workspaces",
            return_value=success
        )
        _mock_fetch_workspaces(mocker, [_test_workspace1])
        _mock_arguments(mocker, _arguments({"unlock_workspaces": True}))

        main()

        unlock_mock.assert_called_once()
        if success:
            fail_mock.assert_not_called()
        else:
            fail_mock.assert_called_once()


def test_patch_working_directories(mocker: MockerFixture) -> None:
    for success in [True, False]:
        fail_mock: MagicMock = mocker.patch("terraform_manager.__main__.fail", return_value=None)
        working_directory_mock: MagicMock = mocker.patch(
            "terraform_manager.entities.terraform.Terraform.set_working_directories",
            return_value=success
        )
        _mock_fetch_workspaces(mocker, [_test_workspace1])

        desired_directory = "test"
        _mock_arguments(mocker, _arguments({"working_directory": desired_directory}))

        main()

        working_directory_mock.assert_called_once_with(desired_directory)
        if success:
            fail_mock.assert_not_called()
        else:
            fail_mock.assert_called_once()


def test_clear_working_directories(mocker: MockerFixture) -> None:
    fail_mock: MagicMock = mocker.patch("terraform_manager.__main__.fail", return_value=None)
    working_directory_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.Terraform.set_working_directories", return_value=True
    )
    _mock_fetch_workspaces(mocker, [_test_workspace1])
    _mock_arguments(mocker, _arguments({"clear_working_directory": True}))

    main()

    working_directory_mock.assert_called_once_with(None)
    fail_mock.assert_not_called()


def test_create_variables_template(mocker: MockerFixture) -> None:
    fail_mock: MagicMock = mocker.patch("terraform_manager.__main__.fail", return_value=None)
    create_mock: MagicMock = mocker.patch(
        "terraform_manager.__main__.create_variables_template", return_value=True
    )
    _mock_arguments(mocker, _arguments({"create_variables_template": True}))

    main()

    create_mock.assert_called_once_with(write_output=True)
    fail_mock.assert_not_called()


def test_create_variables_template_failure(mocker: MockerFixture) -> None:
    fail_mock: MagicMock = mocker.patch("terraform_manager.__main__.fail", return_value=None)
    create_mock: MagicMock = mocker.patch(
        "terraform_manager.__main__.create_variables_template", return_value=False
    )
    _mock_arguments(mocker, _arguments({"create_variables_template": True}))

    main()

    create_mock.assert_called_once_with(write_output=True)
    fail_mock.assert_called_once()


def test_configure_variables(mocker: MockerFixture) -> None:
    for success in [True, False]:
        test_variable = Variable(key="key", value="value")
        fail_mock: MagicMock = mocker.patch("terraform_manager.__main__.fail", return_value=None)
        parse_mock: MagicMock = mocker.patch(
            "terraform_manager.__main__.parse_variables", return_value=[test_variable]
        )
        configure_mock: MagicMock = mocker.patch(
            "terraform_manager.entities.terraform.Terraform.configure_variables",
            return_value=success
        )
        _mock_fetch_workspaces(mocker, [_test_workspace1])

        variables_file = "test.json"
        _mock_arguments(mocker, _arguments({"configure_variables": variables_file}))

        main()

        parse_mock.assert_called_once_with(variables_file, write_output=True)
        configure_mock.assert_called_once_with([test_variable])
        if success:
            fail_mock.assert_not_called()
        else:
            fail_mock.assert_called_once()


def test_configure_variables_nothing_parsed(mocker: MockerFixture) -> None:
    fail_mock: MagicMock = mocker.patch("terraform_manager.__main__.fail", return_value=None)
    parse_mock: MagicMock = mocker.patch(
        "terraform_manager.__main__.parse_variables", return_value=[]
    )
    configure_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.Terraform.configure_variables", return_value=True
    )
    _mock_fetch_workspaces(mocker, [_test_workspace1])

    variables_file = "test.json"
    _mock_arguments(mocker, _arguments({"configure_variables": variables_file}))

    main()

    parse_mock.assert_called_once_with(variables_file, write_output=True)
    configure_mock.assert_not_called()
    fail_mock.assert_called_once()
