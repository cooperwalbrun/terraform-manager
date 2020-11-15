import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from terraform_manager.terraform import credentials
from terraform_manager.terraform.credentials import find_token

_domain: str = "app.terraform.io"
_token: str = "test token"
_sample_credentials_file_contents: str = json.dumps({"credentials": {_domain: {"token": _token}}})


@pytest.fixture(autouse=True)
def clear_token_cache() -> None:
    credentials._cached_token = None


def test_find_token_custom_environment_variable(mocker: Any) -> None:
    mocker.patch.dict(
        "os.environ", {credentials._token_environment_variable_name: _token}, clear=True
    )
    assert find_token(_domain) == _token
    assert find_token(_domain) == _token  # Tests the caching functionality


def _test_find_token_configuration_file(
    mocker: Any, configuration_file_exists: bool, configuration_file_empty: bool, windows: bool
) -> None:
    mocker.patch.dict("os.environ", {}, clear=True)

    mocker.patch(
        # We cannot directly mock the underlying os.name because that causes the entire Python
        # runtime to explode
        "terraform_manager.utilities.utilities.is_windows_operating_system",
        return_value=windows
    )
    mocker.patch("os.path.expandvars", return_value="something")
    mocker.patch("os.path.exists", return_value=configuration_file_exists)

    file_mock: MagicMock = mocker.patch("terraform_manager.terraform.credentials.open")
    mocker.mock_open(
        mock=file_mock,
        read_data=_sample_credentials_file_contents if not configuration_file_empty else ""
    )

    if not configuration_file_exists or configuration_file_empty:
        assert find_token(_domain) is None
    else:
        assert find_token(_domain) == _token


def test_find_token_configuration_file_unix(mocker: Any) -> None:
    _test_find_token_configuration_file(
        mocker=mocker,
        configuration_file_exists=True,
        configuration_file_empty=False,
        windows=False
    )


def test_find_token_configuration_file_windows(mocker: Any) -> None:
    _test_find_token_configuration_file(
        mocker=mocker, configuration_file_exists=True, configuration_file_empty=False, windows=True
    )


def test_find_token_configuration_file_missing(mocker: Any) -> None:
    _test_find_token_configuration_file(
        mocker=mocker, configuration_file_exists=False, configuration_file_empty=True, windows=True
    )


def test_find_token_configuration_file_empty(mocker: Any) -> None:
    _test_find_token_configuration_file(
        mocker=mocker, configuration_file_exists=True, configuration_file_empty=True, windows=True
    )
