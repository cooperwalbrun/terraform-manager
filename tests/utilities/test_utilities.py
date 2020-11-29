from requests import RequestException, Response
from terraform_manager.utilities.utilities import parse_domain, safe_http_request


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
