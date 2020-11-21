import sys
from typing import TypeVar, Callable, Any, List, Optional, Dict

import requests
from terraform_manager.terraform import get_api_headers
from terraform_manager.utilities.throttle import throttle
from terraform_manager.utilities.utilities import safe_http_request, coalesce_domain

A = TypeVar("A")


def _get_next_page(json: Dict[str, Any]) -> Optional[int]:
    if "meta" in json and "pagination" in json["meta"]:
        return json["meta"]["pagination"].get("next-page")
    else:
        return None


def exhaust_pages(
    endpoint: str,
    *,
    json_mapper: Callable[[Any], A],
    write_error_messages: bool = False
) -> List[A]:
    """
    Iterates through every page that will be returned by a given Terraform API endpoint.

    :param endpoint: The full URL of a GET-able Terraform API endpoint (either Terraform Cloud or
                     Enterprise).
    :param json_mapper: A mapping function that takes the value of the "data" field as input and
                        returns a new value (which will be aggregated for all pages).
    :param write_error_messages: Whether to write error messages to STDERR.
    :return: A list of outputs from the json_mapper function.
    """

    current_page = 1
    aggregate = []
    headers = get_api_headers(coalesce_domain(endpoint), write_error_messages=write_error_messages)
    while current_page is not None:
        parameters = {
            # See: https://www.terraform.io/docs/cloud/api/index.html#pagination
            "page[number]": current_page,
            "page[size]": 100
        }
        response = safe_http_request(
            lambda: throttle(lambda: requests.get(endpoint, headers=headers, params=parameters))
        )
        if response.status_code == 200:
            json = response.json()
            if "data" in json:
                aggregate.append(json_mapper(json["data"]))
            current_page = _get_next_page(json)
        else:
            if write_error_messages:
                # yapf: disable
                print((
                    f"Error: the Terraform API returned an error response from {endpoint} with "
                    f"parameters {parameters} - response from the API was {response.json()}"
                ), file=sys.stderr)
                # yapf: enable
            current_page = None
    return aggregate
