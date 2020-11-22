import responses
from pytest_mock import MockerFixture
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform.workspaces import fetch_all

from tests.utilities.tooling import test_workspace, TEST_API_URL, TEST_TERRAFORM_DOMAIN, \
    establish_credential_mocks

_test_organization: str = "test"
_test_api_url: str = f"{TEST_API_URL}/organizations/{_test_organization}/workspaces"

_test_workspace1: Workspace = test_workspace(version="0.13.5")
_test_workspace2: Workspace = test_workspace(version="0.12.28")

# yapf: disable
_test_json = {
    "data": [{
        "id": _test_workspace1.workspace_id,
        "attributes": {
            "auto-apply": _test_workspace1.auto_apply,
            "name": _test_workspace1.name,
            "terraform-version": _test_workspace1.terraform_version,
            "locked": _test_workspace1.is_locked
        }
    }, {
        "id": _test_workspace2.workspace_id,
        "attributes": {
            "auto-apply": _test_workspace2.auto_apply,
            "name": _test_workspace2.name,
            "terraform-version": _test_workspace2.terraform_version,
            "locked": _test_workspace2.is_locked
        }
    }]
}
# yapf: enable


@responses.activate
def test_fetch_all_workspaces(mocker: MockerFixture) -> None:
    establish_credential_mocks(mocker)
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=_test_json,
        status=200
    )
    assert fetch_all(TEST_TERRAFORM_DOMAIN,
                     _test_organization) == [_test_workspace1, _test_workspace2]


@responses.activate
def test_fetch_all_workspaces_with_filter(mocker: MockerFixture) -> None:
    establish_credential_mocks(mocker)
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=_test_json,
        status=200
    )
    assert fetch_all(
        TEST_TERRAFORM_DOMAIN,
        _test_organization,
        workspaces=[_test_workspace2.name],
        blacklist=False
    ) == [_test_workspace2]


@responses.activate
def test_fetch_all_workspaces_with_wildcard_filter(mocker: MockerFixture) -> None:
    establish_credential_mocks(mocker)
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=_test_json,
        status=200
    )
    assert fetch_all(
        TEST_TERRAFORM_DOMAIN, _test_organization, workspaces=["*"], blacklist=False
    ) == [_test_workspace1, _test_workspace2]


@responses.activate
def test_fetch_all_workspaces_with_inverted_filter(mocker: MockerFixture) -> None:
    establish_credential_mocks(mocker)
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=_test_json,
        status=200
    )
    assert fetch_all(
        TEST_TERRAFORM_DOMAIN,
        _test_organization,
        workspaces=[_test_workspace2.name],
        blacklist=True
    ) == [_test_workspace1]


@responses.activate
def test_fetch_all_workspaces_with_inverted_wildcard_filter(mocker: MockerFixture) -> None:
    establish_credential_mocks(mocker)
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=_test_json,
        status=200
    )
    assert fetch_all(
        TEST_TERRAFORM_DOMAIN, _test_organization, workspaces=["*"], blacklist=True
    ) == []


@responses.activate
def test_fetch_all_workspaces_bad_json_response(mocker: MockerFixture) -> None:
    establish_credential_mocks(mocker)
    json = {"data": {"bad json": "test"}}
    responses.add(
        responses.GET,
        f"{_test_api_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=json,
        status=200
    )
    assert fetch_all(TEST_TERRAFORM_DOMAIN, _test_organization) == []
