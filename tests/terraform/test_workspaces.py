import responses
from pytest_mock import MockerFixture
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform.workspaces import fetch_all

_test_organization: str = "test"
_test_terraform_domain: str = "app.terraform.io"
_test_api_url: str = \
    f"https://{_test_terraform_domain}/api/v2/organizations/{_test_organization}/workspaces"
_test_workspace1: Workspace = Workspace("1", "test1", "0.13.5", False, False)
_test_workspace2: Workspace = Workspace("2", "test2", "0.12.28", False, False)
# yapf: disable
_test_json = {
    "data": [{
        "id": "1",
        "attributes": {
            "auto-apply": _test_workspace1.auto_apply,
            "name": _test_workspace1.name,
            "terraform-version": _test_workspace1.terraform_version,
            "locked": _test_workspace1.is_locked
        }
    }, {
        "id": "2",
        "attributes": {
            "auto-apply": _test_workspace2.auto_apply,
            "name": _test_workspace2.name,
            "terraform-version": _test_workspace2.terraform_version,
            "locked": _test_workspace2.is_locked
        }
    }]
}
# yapf: enable


def _establish_mocks(mocker: MockerFixture) -> None:
    mocker.patch("terraform_manager.terraform.credentials.find_token", return_value="test")


@responses.activate
def test_fetch_all_workspaces(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=_test_json,
        status=200
    )
    assert fetch_all(_test_terraform_domain,
                     _test_organization) == [_test_workspace1, _test_workspace2]


@responses.activate
def test_fetch_all_workspaces_with_filter(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=_test_json,
        status=200
    )
    assert fetch_all(
        _test_terraform_domain, _test_organization, workspaces=["test2"], blacklist=False
    ) == [_test_workspace2]


@responses.activate
def test_fetch_all_workspaces_with_wildcard_filter(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=_test_json,
        status=200
    )
    assert fetch_all(
        _test_terraform_domain, _test_organization, workspaces=["test*"], blacklist=False
    ) == [_test_workspace1, _test_workspace2]


@responses.activate
def test_fetch_all_workspaces_with_inverted_filter(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=_test_json,
        status=200
    )
    assert fetch_all(
        _test_terraform_domain, _test_organization, workspaces=["test2"], blacklist=True
    ) == [_test_workspace1]


@responses.activate
def test_fetch_all_workspaces_with_inverted_wildcard_filter(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=_test_json,
        status=200
    )
    assert fetch_all(
        _test_terraform_domain, _test_organization, workspaces=["test*"], blacklist=True
    ) == []


@responses.activate
def test_fetch_all_workspaces_bad_json_response(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    json = {"data": {"bad json": "test"}}
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=json,
        status=200
    )
    assert fetch_all(_test_terraform_domain, _test_organization) == []
