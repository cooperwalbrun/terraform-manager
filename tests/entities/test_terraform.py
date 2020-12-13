import sys
from unittest.mock import MagicMock, call

from pytest_mock import MockerFixture
from terraform_manager.entities.terraform import Terraform
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform import CLOUD_DOMAIN

from tests.utilities.tooling import test_workspace, TEST_TERRAFORM_DOMAIN, TEST_ORGANIZATION

_test_workspace: Workspace = test_workspace(version="0.13.0")


def test_lazy_workspace_fetching(mocker: MockerFixture) -> None:
    fetch_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.fetch_all", return_value=[_test_workspace]
    )
    terraform = Terraform(TEST_TERRAFORM_DOMAIN, TEST_ORGANIZATION, token=None)
    workspaces1 = terraform.workspaces
    workspaces2 = terraform.workspaces
    fetch_mock.assert_called_once()
    assert workspaces1 == workspaces2

    terraform.token = "test"
    workspaces3 = terraform.workspaces
    assert fetch_mock.call_count == 2


def test_configuration_validation_no_tls_against_terraform_cloud(mocker: MockerFixture) -> None:
    fetch_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.fetch_all", return_value=[_test_workspace]
    )
    print_mock: MagicMock = mocker.patch("builtins.print")
    terraform = Terraform(
        CLOUD_DOMAIN,
        TEST_ORGANIZATION,
        workspace_names=[_test_workspace.name],
        no_tls=True,
        write_output=True
    )
    assert not terraform.configuration_is_valid()
    print_mock.assert_called_once_with(
        "Error: you should not disable SSL/TLS when interacting with Terraform Cloud.",
        file=sys.stderr
    )
    assert terraform.workspaces == []
    fetch_mock.assert_not_called()


def test_configuration_validation_unexpected_blacklist_flag(mocker: MockerFixture) -> None:
    for test in [None, []]:
        fetch_mock: MagicMock = mocker.patch(
            "terraform_manager.entities.terraform.fetch_all", return_value=[_test_workspace]
        )
        print_mock: MagicMock = mocker.patch("builtins.print")
        terraform = Terraform(
            TEST_TERRAFORM_DOMAIN,
            TEST_ORGANIZATION,
            workspace_names=test,
            blacklist=True,
            write_output=True
        )
        assert not terraform.configuration_is_valid()
        # yapf: disable
        print_mock.assert_called_once_with((
            "Error: the blacklist flag is only applicable when you specify workspace(s) to filter "
            "on."
        ), file=sys.stderr)
        # yapf: enable
        assert terraform.workspaces == []
        fetch_mock.assert_not_called()


def test_passthrough(mocker: MockerFixture) -> None:
    workspaces = [_test_workspace]

    mocker.patch("terraform_manager.entities.terraform.fetch_all", return_value=workspaces)
    lock_or_unlock_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.lock_or_unlock_workspaces", return_value=True
    )
    summary_mock: MagicMock = mocker.patch("terraform_manager.entities.terraform.write_summary")
    configure_variables_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.configure_variables", return_value=True
    )
    delete_variables_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.delete_variables", return_value=True
    )
    batch_operation_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.batch_operation", return_value=True
    )

    terraform = Terraform(TEST_TERRAFORM_DOMAIN, TEST_ORGANIZATION)

    assert terraform.lock_workspaces()
    assert terraform.unlock_workspaces()
    lock_or_unlock_mock.assert_has_calls([
        call(
            TEST_TERRAFORM_DOMAIN,
            TEST_ORGANIZATION,
            workspaces,
            set_lock=True,
            no_tls=False,
            token=None,
            write_output=False
        ),
        call(
            TEST_TERRAFORM_DOMAIN,
            TEST_ORGANIZATION,
            workspaces,
            set_lock=False,
            no_tls=False,
            token=None,
            write_output=False
        )
    ])

    assert terraform.check_versions("0.13.5")
    assert not terraform.check_versions("0.12.9")

    terraform.write_summary()
    summary_mock.assert_called_once_with(
        TEST_TERRAFORM_DOMAIN,
        TEST_ORGANIZATION,
        workspaces,
        targeting_specific_workspaces=False,
        write_output=False
    )

    variables = []
    assert terraform.configure_variables(variables)
    configure_variables_mock.assert_called_once_with(
        TEST_TERRAFORM_DOMAIN,
        TEST_ORGANIZATION,
        workspaces,
        variables=variables,
        no_tls=False,
        token=None,
        write_output=False
    )

    assert terraform.delete_variables(variables)
    delete_variables_mock.assert_called_once_with(
        TEST_TERRAFORM_DOMAIN,
        TEST_ORGANIZATION,
        workspaces,
        variables=variables,
        no_tls=False,
        token=None,
        write_output=False
    )

    assert terraform.set_working_directories("test")
    assert terraform.set_execution_modes("local")
    assert not terraform.set_execution_modes("something invalid")
    assert terraform.set_auto_apply(False)
    assert terraform.set_versions("1000.0.0")
    assert terraform.set_speculative(False)
    assert batch_operation_mock.call_count == 5


def test_is_terraform_cloud() -> None:
    domains = [CLOUD_DOMAIN, CLOUD_DOMAIN.upper()]
    for domain in domains:
        assert Terraform(domain, TEST_ORGANIZATION).is_terraform_cloud
    domains = ["something.mycompany.com", "app.company.io"]
    for domain in domains:
        assert not Terraform(domain, TEST_ORGANIZATION).is_terraform_cloud


def test_set_execution_modes(mocker: MockerFixture) -> None:
    for write_output in [True, False]:
        print_mock: MagicMock = mocker.patch("builtins.print")

        cloud_terraform = Terraform(
            TEST_TERRAFORM_DOMAIN, TEST_ORGANIZATION, write_output=write_output
        )
        enterprise_domain = "something.company.com"
        enterprise_terraform = Terraform(
            enterprise_domain, TEST_ORGANIZATION, write_output=write_output
        )

        for terraform in [cloud_terraform, enterprise_terraform]:
            invalid = "invalid"
            assert not terraform.set_execution_modes(invalid)
            if write_output:
                print_mock.assert_called_once_with(
                    f"Error: invalid execution-mode specified: {invalid}", file=sys.stderr
                )
                print_mock.reset_mock()
            else:
                print_mock.assert_not_called()

        assert not enterprise_terraform.set_execution_modes("agent", agent_pool_id="something")
        if write_output:
            # yapf: disable
            print_mock.assert_called_once_with((
                f'Error: desired execution-mode is "agent" but you are not targeting Terraform '
                f'Cloud (selected domain is "{enterprise_domain}").'
            ), file=sys.stderr)
            # yapf: enable
            print_mock.reset_mock()
        else:
            print_mock.assert_not_called()

        assert not cloud_terraform.set_execution_modes("agent")
        if write_output:
            print_mock.assert_called_once_with(
                f'Error: desired execution-mode is "agent" but no agent-pool-id was specified.',
                file=sys.stderr
            )
            print_mock.reset_mock()
        else:
            print_mock.assert_not_called()

        for test in [None, ""]:
            assert not cloud_terraform.set_execution_modes("agent", agent_pool_id=test)
            if write_output:
                print_mock.assert_called_once_with(
                    f'Error: desired execution-mode is "agent" but no agent-pool-id was specified.',
                    file=sys.stderr
                )
                print_mock.reset_mock()
            else:
                print_mock.assert_not_called()

        for test in ["remote", "local"]:
            for terraform in [cloud_terraform, enterprise_terraform]:
                assert not terraform.set_execution_modes(test, agent_pool_id="something")
                if write_output:
                    # yapf: disable
                    print_mock.assert_called_once_with((
                        f'Error: desired execution-mode is "{test}" but an agent-pool-id was '
                        f'specified.'
                    ), file=sys.stderr)
                    # yapf: enable
                    print_mock.reset_mock()
                else:
                    print_mock.assert_not_called()
