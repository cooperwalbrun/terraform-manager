from unittest.mock import MagicMock

from pytest_mock import MockerFixture
from terraform_manager.entities.terraform import Terraform

from tests.utilities.tooling import test_workspace, TEST_TERRAFORM_DOMAIN, TEST_ORGANIZATION


def test_lazy_workspace_fetching(mocker: MockerFixture) -> None:
    test = test_workspace()
    fetch_mock: MagicMock = mocker.patch(
        "terraform_manager.entities.terraform.fetch_all", return_value=[test]
    )
    terraform = Terraform(TEST_TERRAFORM_DOMAIN, TEST_ORGANIZATION, token=None)
    workspaces1 = terraform.workspaces
    workspaces2 = terraform.workspaces
    fetch_mock.assert_called_once()
    assert workspaces1 == workspaces2

    terraform.token = "test"
    workspaces3 = terraform.workspaces
    assert fetch_mock.call_count == 2
