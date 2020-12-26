from requests import RequestException, Response
from terraform_manager.utilities.utilities import parse_domain, safe_http_request, safe_deep_get, \
    convert_timestamp_to_unix_time, convert_hashicorp_timestamp_to_unix_time


def test_parse_url() -> None:
    cloud_domain = "app.terraform.io"
    terraform_cloud_tests = [
        f"https://{cloud_domain}/app/someorganization",
        f"http://{cloud_domain}/app/someorganization",
        cloud_domain,
        f"{cloud_domain}/some/path"
    ]
    for test in terraform_cloud_tests:
        assert parse_domain(test) == cloud_domain

    # yapf: disable
    enterprise_domain1 = "myserver.terraform.com"
    enterprise_domain2 = "terraform.com"
    terraform_enterprise_tests = [
        (f"https://{enterprise_domain1}", enterprise_domain1),
        (f"http://{enterprise_domain1}", enterprise_domain1),
        (f"https://{enterprise_domain1}/app/someorganization", enterprise_domain1),
        (f"https://{enterprise_domain2}", enterprise_domain2),
        (enterprise_domain2, enterprise_domain2),
        (f"{enterprise_domain2}/some/path", enterprise_domain2),
        ("https://terraform", "terraform")
    ]
    # yapf: enable
    for test, expected_result in terraform_enterprise_tests:
        assert parse_domain(test) == expected_result


def test_safe_http_request() -> None:
    message = "Testing dangerous HTTP activity"

    def fail() -> Response:
        raise RequestException(message)

    response = safe_http_request(fail)
    assert response.json() == {"terraform-manager": {"error": message, "status": 500}}


def test_safe_deep_get() -> None:
    assert safe_deep_get({}, []) is None
    assert safe_deep_get({}, ["test", "test"]) is None
    assert safe_deep_get({"test": {"test": "test"}}, ["test", "test"]) == "test"
    for test in ["", None]:
        assert safe_deep_get({"test": {"test": test}}, []) is None
        assert safe_deep_get({"test": test}, ["test", "test"]) is None
        assert safe_deep_get({"test": test}, ["test", "test", "test"]) is None


def test_convert_timestamp_to_unix_time() -> None:
    # yapf: disable
    tests = [
        ("2017-11-28T22:52:46", "%Y-%m-%dT%H:%M:%S", 1511909566),
        ("2017-11-28T22:52:46UTC", "%Y-%m-%dT%H:%M:%S%Z", 1511909566),
        ("2017-11-28T22:52:46GMT", "%Y-%m-%dT%H:%M:%S%Z", 1511909566),
        ("something bad", "%Y", None)
    ]
    # yapf: enable
    for timestamp, timestamp_format, expected in tests:
        assert convert_timestamp_to_unix_time(timestamp, timestamp_format) == expected


def test_convert_hashicorp_timestamp_to_unix_time() -> None:
    # yapf: disable
    tests = [
        ("2020-11-05T04:31:25+00:00", 1604550685),
        ("2020-11-05T04:31:25+04:00", 1604536285),
        ("2020-11-05T04:31:25-04:00", None),
        ("2017-11-28T22:52:46", None),
        ("something bad", None)
    ]
    # yapf: enable
    for timestamp, expected in tests:
        assert convert_hashicorp_timestamp_to_unix_time(timestamp) == expected
