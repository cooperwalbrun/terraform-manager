from pytest_mock import MockerFixture
from terraform_manager.terraform import get_api_headers, HTTP_CONTENT_TYPE

from tests.utilities.tooling import TEST_TERRAFORM_DOMAIN


def test_get_api_headers(mocker: MockerFixture) -> None:
    token = "test"
    mocker.patch("terraform_manager.terraform.find_token", return_value=token)
    headers = get_api_headers(TEST_TERRAFORM_DOMAIN, token=None)
    assert headers == {"Authorization": f"Bearer {token}", "Content-Type": HTTP_CONTENT_TYPE}

    token = "test123"
    headers = get_api_headers(TEST_TERRAFORM_DOMAIN, token=token)
    assert headers == {"Authorization": f"Bearer {token}", "Content-Type": HTTP_CONTENT_TYPE}


def test_get_api_headers_missing_token(mocker: MockerFixture) -> None:
    mocker.patch("terraform_manager.terraform.find_token", return_value=None)
    headers = get_api_headers(TEST_TERRAFORM_DOMAIN, token=None)
    assert headers == {"Content-Type": HTTP_CONTENT_TYPE}
