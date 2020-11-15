from typing import Any, List, Dict

import responses
from terraform_manager.terraform.pagination import exhaust_pages

_test_url: str = "http://some.endpoint/thing"


def _simple_mapper(data: List[Dict[str, str]]) -> List[str]:
    aggregation = []
    for entity in data:
        aggregation.append(entity["objectname"])
    return aggregation


def _establish_mocks(mocker: Any) -> None:
    mocker.patch("terraform_manager.terraform.credentials.find_token", return_value="test")


@responses.activate
def test_exhaust_pages_single_page(mocker: Any) -> None:
    _establish_mocks(mocker)
    json = {"data": [{"objectname": "test1"}, {"objectname": "test2"}]}
    responses.add(responses.GET, _test_url, json=json, status=200)
    assert exhaust_pages(_test_url, _simple_mapper) == [["test1", "test2"]]


@responses.activate
def test_exhaust_pages_single_page_with_meta_block(mocker: Any) -> None:
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
    responses.add(responses.GET, _test_url, json=json, status=200)
    assert exhaust_pages(_test_url, _simple_mapper) == [["test1", "test2"]]


@responses.activate
def test_exhaust_pages_bad_json_response(mocker: Any) -> None:
    _establish_mocks(mocker)
    json = {"not data": {}}
    responses.add(responses.GET, _test_url, json=json, status=200)
    assert exhaust_pages(_test_url, _simple_mapper) == []


@responses.activate
def test_exhaust_pages_error(mocker: Any) -> None:
    _establish_mocks(mocker)
    json = {"errors": [{"detail": "Something bad happened.", "status": 500, "title": "Oops"}]}
    responses.add(responses.GET, _test_url, json=json, status=500)
    assert exhaust_pages(_test_url, _simple_mapper) == []


@responses.activate
def test_exhaust_pages_multiple_pages(mocker: Any) -> None:
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
