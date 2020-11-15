from typing import Any

import responses
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform.workspaces import fetch_all

_test_organization: str = "test"
_test_terraform_url: str = "https://some.endpoint"
_test_api_url: str = f"{_test_terraform_url}/api/v2/organizations/{_test_organization}/workspaces"
# yapf: disable
_test_json = {
    "data": [{
        "id": "1",
        "attributes": {
            "auto-apply": False, "name": "test1", "terraform-version": "0.13.5", "locked": False
        }
    }, {
        "id": "2",
        "attributes": {
            "auto-apply": False, "name": "test2", "terraform-version": "0.12.28", "locked": False
        }
    }]
}
# yapf: enable


def _establish_mocks(mocker: Any) -> None:
    mocker.patch("terraform_manager.terraform.credentials.find_token", return_value="test")


@responses.activate
def test_fetch_all_workspaces(mocker: Any) -> None:
    _establish_mocks(mocker)
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=_test_json,
        status=200
    )
    assert fetch_all(
        _test_organization, url=_test_terraform_url
    ) == [
        Workspace("1", "test1", "0.13.5", False, False),
        Workspace("2", "test2", "0.12.28", False, False)
    ]


@responses.activate
def test_fetch_all_workspaces_with_filter(mocker: Any) -> None:
    _establish_mocks(mocker)
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=_test_json,
        status=200
    )
    assert fetch_all(
        _test_organization, workspaces=["test2"], url=_test_terraform_url
    ) == [Workspace("2", "test2", "0.12.28", False, False)]


@responses.activate
def test_fetch_all_workspaces_bad_json_response(mocker: Any) -> None:
    _establish_mocks(mocker)
    json = {"data": {"bad json": "test"}}
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=json,
        status=200
    )
    assert fetch_all(_test_organization, url=_test_terraform_url) == []
