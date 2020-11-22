import random
import string

from pytest_mock import MockerFixture
from terraform_manager.entities.workspace import Workspace

TEST_ORGANIZATION: str = "test"
TEST_TERRAFORM_DOMAIN: str = "app.terraform.io"
TEST_API_URL: str = f"https://{TEST_TERRAFORM_DOMAIN}/api/v2"


def establish_credential_mocks(mocker: MockerFixture) -> None:
    mocker.patch("terraform_manager.terraform.credentials.find_token", return_value="test")


def test_workspace(
    version: str = "0.13.1", locked: bool = False, working_directory: str = ""
) -> Workspace:
    letters = string.ascii_lowercase
    return Workspace(
        "".join([random.choice(letters) for _ in range(5)]),
        "".join([random.choice(letters) for _ in range(5)]),
        version,
        False,
        locked,
        working_directory
    )
