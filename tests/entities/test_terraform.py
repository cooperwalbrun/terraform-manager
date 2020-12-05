from unittest.mock import MagicMock, call

from pytest_mock import MockerFixture
from terraform_manager.entities.terraform import Terraform
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform.versions import group_by_version

from tests.utilities.tooling import test_workspace, TEST_TERRAFORM_DOMAIN, TEST_ORGANIZATION

_test_workspace: Workspace = test_workspace()


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


def test_passthrough(mocker: MockerFixture) -> None:
    workspaces = [_test_workspace]
    mocker.patch("terraform_manager.entities.terraform.fetch_all", return_value=workspaces)
    lock_or_unlock_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.lock_or_unlock_workspaces", return_value=True
    )
    check_versions_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.check_versions", return_value=True
    )
    patch_versions_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.patch_versions", return_value=True
    )
    version_summary_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.write_version_summary"
    )
    patch_working_directories_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.patch_working_directories", return_value=True
    )
    configure_variables_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.configure_variables", return_value=True
    )
    delete_variables_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.delete_variables", return_value=True
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

    terraform_version = "0.13.5"
    assert terraform.check_versions(terraform_version)
    check_versions_mock.assert_called_once_with(workspaces, terraform_version)

    assert terraform.patch_versions(terraform_version)
    patch_versions_mock.assert_called_once_with(
        TEST_TERRAFORM_DOMAIN,
        TEST_ORGANIZATION,
        workspaces,
        new_version=terraform_version,
        no_tls=False,
        token=None,
        write_output=False
    )

    terraform.write_version_summary()
    version_summary_mock.assert_called_once_with(
        TEST_TERRAFORM_DOMAIN, TEST_ORGANIZATION, False, group_by_version(workspaces)
    )

    working_directory = "test"
    assert terraform.set_working_directories(working_directory)
    patch_working_directories_mock.assert_called_once_with(
        TEST_TERRAFORM_DOMAIN,
        TEST_ORGANIZATION,
        workspaces,
        new_working_directory=working_directory,
        no_tls=False,
        token=None,
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
