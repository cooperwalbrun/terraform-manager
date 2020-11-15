from typing import Any, List, Dict

import responses
from pytest_mock import MockerFixture
from terraform_manager.terraform.pagination import exhaust_pages

_test_url: str = "http://some.endpoint/thing"


def _simple_mapper(data: List[Dict[str, str]]) -> List[str]:
    aggregation = []
    for entity in data:
        aggregation.append(entity["objectname"])
    return aggregation


def _establish_mocks(mocker: MockerFixture) -> None:
    mocker.patch("terraform_manager.terraform.credentials.find_token", return_value="test")


@responses.activate
def test_exhaust_pages_single_page(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    json = {"data": [{"objectname": "test1"}, {"objectname": "test2"}]}
    responses.add(
        responses.GET,
        f"{_test_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=json,
        status=200
    )
    assert exhaust_pages(_test_url, _simple_mapper) == [["test1", "test2"]]


@responses.activate
def test_exhaust_pages_single_page_with_meta_block(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    json = {
        "data": [{
            "objectname": "test1"
        }, {
            "objectname": "test2"
        }],
        "meta": {
            "pagination": {
                "next-page": None
            }
        }
    }
    responses.add(
        responses.GET,
        f"{_test_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=json,
        status=200
    )
    assert exhaust_pages(_test_url, _simple_mapper) == [["test1", "test2"]]


@responses.activate
def test_exhaust_pages_bad_json_response(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    json = {"not data": {}}
    responses.add(
        responses.GET,
        f"{_test_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=json,
        status=200
    )
    assert exhaust_pages(_test_url, _simple_mapper) == []


@responses.activate
def test_exhaust_pages_error_http_response(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    status_code = 500
    json = {
        "errors": [{
            "detail": "Something bad happened.", "status": status_code, "title": "Oops"
        }]
    }
    responses.add(
        responses.GET,
        f"{_test_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=json,
        status=status_code
    )
    assert exhaust_pages(_test_url, _simple_mapper) == []


@responses.activate
def test_exhaust_pages_multiple_pages(mocker: MockerFixture) -> None:
    _establish_mocks(mocker)
    json_page1 = {
        "data": [{
            "objectname": "test1"
        }, {
            "objectname": "test2"
        }],
        "meta": {
            "pagination": {
                "next-page": 2
            }
        }
    }
    json_page2 = {
        "data": [{
            "objectname": "test3"
        }, {
            "objectname": "test4"
        }],
        "meta": {
            "pagination": {
                "next-page": None
            }
        }
    }
    responses.add(
        responses.GET,
        f"{_test_url}?page[size]=100&page[number]=1",
        match_querystring=True,
        json=json_page1,
        status=200
    )
    responses.add(
        responses.GET,
        f"{_test_url}?page[size]=100&page[number]=2",
        match_querystring=True,
        json=json_page2,
        status=200
    )
    assert exhaust_pages(_test_url, _simple_mapper) == [["test1", "test2"], ["test3", "test4"]]
