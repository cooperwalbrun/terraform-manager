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
    "silent": False,
    "version_summary": False,
    "lock_workspaces": False,
    "unlock_workspaces": False,
    "clear_working_directory": False,
    "create_variables_template": False,
    "enable_auto_apply": False,
    "disable_auto_apply": False
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


def _mock_sys_argv_arguments(
    mocker: MockerFixture, *, arguments: Optional[List[str]] = None
) -> MagicMock:
    return mocker.patch(
        "terraform_manager.__main__._get_arguments",
        return_value=["-o", TEST_ORGANIZATION] if arguments is None else arguments
    )


def _mock_parsed_arguments(mocker: MockerFixture, arguments: Dict[str, Any]) -> MagicMock:
    return mocker.patch("terraform_manager.__main__._parse_arguments", return_value=arguments)


def _mock_get_group_arguments(
    mocker: MockerFixture,
    selection: Optional[str] = None,
    special: Optional[str] = None
) -> (MagicMock, MagicMock):
    return (
        mocker.patch("terraform_manager.__main__._get_selection_argument", return_value=selection),
        mocker.patch("terraform_manager.__main__._get_special_argument", return_value=special)
    )


def _mock_cli_fail(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("terraform_manager.cli_handlers.fail", return_value=None)


def _error_message(text: str) -> call:
    return call(text, file=sys.stderr)


def test_no_arguments(mocker: MockerFixture) -> None:
    _mock_sys_argv_arguments(mocker, arguments=[])
    parser_mock: MagicMock = mocker.patch("terraform_manager.__main__._parser.error")
    _mock_parsed_arguments(mocker, _bool_flags)
    main()
    parser_mock.assert_called_once_with("You must specify at least one argument.")


def test_selection_operation_without_organization(mocker: MockerFixture) -> None:
    for silent in [True, False]:
        _mock_sys_argv_arguments(mocker)
        parser_fail_mock: MagicMock = mocker.patch("terraform_manager.__main__._parser_fail")
        parser_mock: MagicMock = mocker.patch("terraform_manager.__main__._parser.error")
        _mock_parsed_arguments(mocker, {**_bool_flags, "silent": silent, "blacklist": True})
        _mock_get_group_arguments(mocker)
        main()
        if silent:
            parser_mock.assert_not_called()
            parser_fail_mock.assert_called_once()
        else:
            parser_mock.assert_called_once_with("You must specify an organization to target.")
            parser_fail_mock.assert_not_called()


def test_selection_criteria_without_operation(mocker: MockerFixture) -> None:
    for silent in [True, False]:
        _mock_sys_argv_arguments(mocker)
        parser_fail_mock: MagicMock = mocker.patch("terraform_manager.__main__._parser_fail")
        parser_mock: MagicMock = mocker.patch("terraform_manager.__main__._parser.error")
        _mock_fetch_workspaces(mocker, [_test_workspace1])
        _mock_parsed_arguments(mocker, _arguments({"silent": silent}))
        _mock_get_group_arguments(mocker)
        main()
        if silent:
            parser_mock.assert_not_called()
            parser_fail_mock.assert_called_once()
        else:
            parser_mock.assert_called_once_with(
                "Unable to determine which operation you are attempting to perform."
            )
            parser_fail_mock.assert_not_called()


def test_incompatible_argument_groups(mocker: MockerFixture) -> None:
    selection_flags = [
        "-o",
        "--organization",
        "--domain",
        "--no-tls",
        "--no-ssl"
        "-w",
        "--workspaces",
        "-b",
        "--blacklist"
    ]
    special_flags = ["--create-vars-template"]
    for selection in selection_flags:
        for special in special_flags:
            _mock_sys_argv_arguments(mocker)
            parser_mock: MagicMock = mocker.patch("terraform_manager.__main__._parser.error")
            _mock_get_group_arguments(mocker, selection=selection, special=special)
            main()
            parser_mock.assert_called_once_with((
                f"You cannot specify any selection arguments (such as {selection}) at the same "
                f"time as {special}."
            ))


def test_no_tls_against_terraform_cloud(mocker: MockerFixture) -> None:
    for silent in [True, False]:
        _mock_sys_argv_arguments(mocker)
        print_mock: MagicMock = mocker.patch("builtins.print")
        fail_mock: MagicMock = _mock_cli_fail(mocker)
        _mock_fetch_workspaces(mocker, [])
        _mock_parsed_arguments(mocker, _arguments({"silent": silent, "no_tls": True}))
        _mock_get_group_arguments(mocker)

        main()

        if silent:
            print_mock.assert_not_called()
        else:
            print_mock.assert_has_calls([
                _error_message(
                    "Error: you should not disable SSL/TLS when interacting with Terraform Cloud."
                )
            ])
            assert print_mock.call_count == 1
        fail_mock.assert_called_once()


def test_unexpected_blacklist_flag(mocker: MockerFixture) -> None:
    for silent in [True, False]:
        _mock_sys_argv_arguments(mocker)
        print_mock: MagicMock = mocker.patch("builtins.print")
        fail_mock: MagicMock = _mock_cli_fail(mocker)
        _mock_fetch_workspaces(mocker, [])
        _mock_parsed_arguments(mocker, _arguments({"silent": silent, "blacklist": True}))
        _mock_get_group_arguments(mocker)

        main()

        if silent:
            print_mock.assert_not_called()
        else:
            print_mock.assert_has_calls([
                _error_message((
                    "Error: the blacklist flag is only applicable when you specify workspace(s) to "
                    "filter on."
                ))
            ])
            assert print_mock.call_count == 1
        fail_mock.assert_called_once()


def test_no_workspaces_selected(mocker: MockerFixture) -> None:
    for silent in [True, False]:
        _mock_sys_argv_arguments(mocker)
        print_mock: MagicMock = mocker.patch("builtins.print")
        fail_mock: MagicMock = _mock_cli_fail(mocker)
        _mock_fetch_workspaces(mocker, [])
        _mock_parsed_arguments(mocker, _arguments({"silent": silent}))
        _mock_get_group_arguments(mocker)

        main()

        if silent:
            print_mock.assert_not_called()
        else:
            print_mock.assert_has_calls([
                _error_message("Error: no workspaces could be found in your organization.")
            ])
            assert print_mock.call_count == 1
        fail_mock.assert_called_once()


def test_no_workspaces_selected_with_filter(mocker: MockerFixture) -> None:
    for silent in [True, False]:
        _mock_sys_argv_arguments(mocker)
        print_mock: MagicMock = mocker.patch("builtins.print")
        fail_mock: MagicMock = _mock_cli_fail(mocker)
        _mock_fetch_workspaces(mocker, [])
        _mock_parsed_arguments(
            mocker,
            _arguments({
                "silent": silent, "workspaces": [_test_workspace1.name, _test_workspace2.name]
            })
        )
        _mock_get_group_arguments(mocker)

        main()

        if silent:
            print_mock.assert_not_called()
        else:
            print_mock.assert_has_calls([
                _error_message(
                    "Error: no workspaces could be found with these name(s): {}, {}".format(
                        _test_workspace1.name, _test_workspace2.name
                    )
                )
            ])
            assert print_mock.call_count == 1
        fail_mock.assert_called_once()


def test_version_summary(mocker: MockerFixture) -> None:
    _mock_sys_argv_arguments(mocker)
    fail_mock: MagicMock = _mock_cli_fail(mocker)
    summary_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.Terraform.write_version_summary", return_value=None
    )
    _mock_fetch_workspaces(mocker, [_test_workspace1])
    _mock_parsed_arguments(mocker, _arguments({"version_summary": True}))
    _mock_get_group_arguments(mocker)

    main()

    summary_mock.assert_called_once()
    fail_mock.assert_not_called()


def test_set_versions(mocker: MockerFixture) -> None:
    for success in [True, False]:
        _mock_sys_argv_arguments(mocker)
        fail_mock: MagicMock = _mock_cli_fail(mocker)
        patch_mock: MagicMock = mocker.patch(
            "terraform_manager.entities.terraform.Terraform.set_versions", return_value=success
        )
        desired_version = "0.13.5"
        _mock_fetch_workspaces(mocker, [_test_workspace1])
        _mock_parsed_arguments(mocker, _arguments({"terraform_version": desired_version}))
        _mock_get_group_arguments(mocker)

        main()

        patch_mock.assert_called_once_with(desired_version)
        if success:
            fail_mock.assert_not_called()
        else:
            fail_mock.assert_called_once()


def test_set_versions_invalid_version(mocker: MockerFixture) -> None:
    for silent in [True, False]:
        _mock_sys_argv_arguments(mocker)
        print_mock: MagicMock = mocker.patch("builtins.print")
        fail_mock: MagicMock = _mock_cli_fail(mocker)
        desired_version = "NOT-A-VALID-SEMANTIC-VERSION"
        _mock_fetch_workspaces(mocker, [_test_workspace1])
        _mock_parsed_arguments(
            mocker, _arguments({
                "silent": silent, "terraform_version": desired_version
            })
        )
        _mock_get_group_arguments(mocker)

        main()

        if silent:
            print_mock.assert_not_called()
        else:
            print_mock.assert_has_calls([
                _error_message(
                    f"Error: the version you specified ({desired_version}) is not valid."
                )
            ])
            assert print_mock.call_count == 1
        fail_mock.assert_called_once()


def test_set_versions_downgrade_version(mocker: MockerFixture) -> None:
    for silent in [True, False]:
        _mock_sys_argv_arguments(mocker)
        print_mock: MagicMock = mocker.patch("builtins.print")
        fail_mock: MagicMock = _mock_cli_fail(mocker)
        check_mock: MagicMock = mocker.patch(
            "terraform_manager.entities.terraform.Terraform.check_versions", return_value=False
        )
        _mock_fetch_workspaces(mocker, [_test_workspace1])
        # The version specified below does not actually matter for this test because we are forcing
        # False to return from check_versions with the mock above
        desired_version = "0.13.0"
        _mock_parsed_arguments(
            mocker, _arguments({
                "silent": silent, "terraform_version": desired_version
            })
        )
        _mock_get_group_arguments(mocker)

        main()

        check_mock.assert_called_once_with(desired_version)
        if silent:
            print_mock.assert_not_called()
        else:
            print_mock.assert_has_calls([
                _error_message((
                    "Error: at least one of the target workspaces has a version newer than the one "
                    "you are attempting to change to. No workspaces were updated."
                ))
            ])
            assert print_mock.call_count == 1
        fail_mock.assert_called_once()


def test_lock_workspaces(mocker: MockerFixture) -> None:
    for operation in ["lock_workspaces", "unlock_workspaces"]:
        for success in [True, False]:
            _mock_sys_argv_arguments(mocker)
            fail_mock: MagicMock = _mock_cli_fail(mocker)
            lock_mock: MagicMock = mocker.patch(
                f"terraform_manager.entities.terraform.Terraform.{operation}", return_value=success
            )
            _mock_fetch_workspaces(mocker, [_test_workspace1])
            _mock_parsed_arguments(mocker, _arguments({operation: True}))
            _mock_get_group_arguments(mocker)

            main()

            lock_mock.assert_called_once()
            if success:
                fail_mock.assert_not_called()
            else:
                fail_mock.assert_called_once()


def test_enable_auto_apply(mocker: MockerFixture) -> None:
    for operation in ["enable_auto_apply", "disable_auto_apply"]:
        for success in [True, False]:
            _mock_sys_argv_arguments(mocker)
            fail_mock: MagicMock = _mock_cli_fail(mocker)
            auto_apply_mock: MagicMock = mocker.patch(
                "terraform_manager.entities.terraform.Terraform.set_auto_apply",
                return_value=success
            )
            _mock_fetch_workspaces(mocker, [_test_workspace1])
            _mock_parsed_arguments(mocker, _arguments({operation: True}))
            _mock_get_group_arguments(mocker)

            main()

            auto_apply_mock.assert_called_once()
            if success:
                fail_mock.assert_not_called()
            else:
                fail_mock.assert_called_once()


def test_patch_working_directories(mocker: MockerFixture) -> None:
    for success in [True, False]:
        _mock_sys_argv_arguments(mocker)
        fail_mock: MagicMock = _mock_cli_fail(mocker)
        working_directory_mock: MagicMock = mocker.patch(
            "terraform_manager.entities.terraform.Terraform.set_working_directories",
            return_value=success
        )
        _mock_fetch_workspaces(mocker, [_test_workspace1])

        desired_directory = "test"
        _mock_parsed_arguments(mocker, _arguments({"working_directory": desired_directory}))
        _mock_get_group_arguments(mocker)

        main()

        working_directory_mock.assert_called_once_with(desired_directory)
        if success:
            fail_mock.assert_not_called()
        else:
            fail_mock.assert_called_once()


def test_clear_working_directories(mocker: MockerFixture) -> None:
    _mock_sys_argv_arguments(mocker)
    fail_mock: MagicMock = _mock_cli_fail(mocker)
    working_directory_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.Terraform.set_working_directories", return_value=True
    )
    _mock_fetch_workspaces(mocker, [_test_workspace1])
    _mock_parsed_arguments(mocker, _arguments({"clear_working_directory": True}))
    _mock_get_group_arguments(mocker)

    main()

    working_directory_mock.assert_called_once_with(None)
    fail_mock.assert_not_called()


def test_patch_execution_modes(mocker: MockerFixture) -> None:
    for success in [True, False]:
        _mock_sys_argv_arguments(mocker)
        fail_mock: MagicMock = _mock_cli_fail(mocker)
        working_directory_mock: MagicMock = mocker.patch(
            "terraform_manager.entities.terraform.Terraform.set_execution_modes",
            return_value=success
        )
        _mock_fetch_workspaces(mocker, [_test_workspace1])

        desired_execution_mode = "remote"
        _mock_parsed_arguments(mocker, _arguments({"execution_mode": desired_execution_mode}))
        _mock_get_group_arguments(mocker)

        main()

        working_directory_mock.assert_called_once_with(desired_execution_mode)
        if success:
            fail_mock.assert_not_called()
        else:
            fail_mock.assert_called_once()


def test_create_variables_template(mocker: MockerFixture) -> None:
    _mock_sys_argv_arguments(mocker)
    fail_mock: MagicMock = _mock_cli_fail(mocker)
    create_mock: MagicMock = mocker.patch(
        "terraform_manager.cli_handlers.variables.create_variables_template", return_value=True
    )
    _mock_parsed_arguments(mocker, _arguments({"create_variables_template": True}))
    _mock_get_group_arguments(mocker)

    main()

    create_mock.assert_called_once_with(write_output=True)
    fail_mock.assert_not_called()


def test_create_variables_template_failure(mocker: MockerFixture) -> None:
    _mock_sys_argv_arguments(mocker)
    fail_mock: MagicMock = _mock_cli_fail(mocker)
    create_mock: MagicMock = mocker.patch(
        "terraform_manager.cli_handlers.variables.create_variables_template", return_value=False
    )
    _mock_parsed_arguments(mocker, _arguments({"create_variables_template": True}))
    _mock_get_group_arguments(mocker)

    main()

    create_mock.assert_called_once_with(write_output=True)
    fail_mock.assert_called_once()


def test_configure_variables(mocker: MockerFixture) -> None:
    for success in [True, False]:
        _mock_sys_argv_arguments(mocker)
        test_variable = Variable(key="key", value="value")
        fail_mock: MagicMock = _mock_cli_fail(mocker)
        parse_mock: MagicMock = mocker.patch(
            "terraform_manager.__main__.cli_handlers.parse_variables", return_value=[test_variable]
        )
        configure_mock: MagicMock = mocker.patch(
            "terraform_manager.entities.terraform.Terraform.configure_variables",
            return_value=success
        )
        _mock_fetch_workspaces(mocker, [_test_workspace1])

        variables_file = "test.json"
        _mock_parsed_arguments(mocker, _arguments({"configure_variables": variables_file}))
        _mock_get_group_arguments(mocker)

        main()

        parse_mock.assert_called_once_with(variables_file, write_output=True)
        configure_mock.assert_called_once_with([test_variable])
        if success:
            fail_mock.assert_not_called()
        else:
            fail_mock.assert_called_once()


def test_configure_variables_nothing_parsed(mocker: MockerFixture) -> None:
    _mock_sys_argv_arguments(mocker)
    fail_mock: MagicMock = _mock_cli_fail(mocker)
    parse_mock: MagicMock = mocker.patch(
        "terraform_manager.cli_handlers.parse_variables", return_value=[]
    )
    configure_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.Terraform.configure_variables", return_value=True
    )
    _mock_fetch_workspaces(mocker, [_test_workspace1])

    variables_file = "test.json"
    _mock_parsed_arguments(mocker, _arguments({"configure_variables": variables_file}))
    _mock_get_group_arguments(mocker)

    main()

    parse_mock.assert_called_once_with(variables_file, write_output=True)
    configure_mock.assert_not_called()
    fail_mock.assert_called_once()


def test_delete_variables(mocker: MockerFixture) -> None:
    for success in [True, False]:
        _mock_sys_argv_arguments(mocker)
        fail_mock: MagicMock = _mock_cli_fail(mocker)
        delete_mock: MagicMock = mocker.patch(
            "terraform_manager.entities.terraform.Terraform.delete_variables", return_value=success
        )
        _mock_fetch_workspaces(mocker, [_test_workspace1])

        variables_to_delete = ["some-key"]
        _mock_parsed_arguments(mocker, _arguments({"delete_variables": variables_to_delete}))
        _mock_get_group_arguments(mocker)

        main()

        delete_mock.assert_called_once_with(variables_to_delete)
        if success:
            fail_mock.assert_not_called()
        else:
            fail_mock.assert_called_once()
