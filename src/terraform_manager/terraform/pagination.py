import sys
from typing import TypeVar, Callable, Any, List, Optional, Dict

import requests
from terraform_manager.terraform import credentials
from terraform_manager.utilities.throttle import throttle
from terraform_manager.utilities.utilities import coalesce_domain

A = TypeVar("A")


def _get_next_page(json: Dict[str, Any]) -> Optional[int]:
    if "meta" in json and "pagination" in json["meta"]:
        return json["meta"]["pagination"].get("next-page")
    else:
        return None


def exhaust_pages(url: str, json_mapper: Callable[[Any], A]) -> List[A]:
    """
    Iterates through every page that will be returned by a given Terraform API endpoint.

    :param url: The URL endpoint to paginate.
    :param json_mapper: A mapping function that takes the value of the "data" field as input and
                        returns a new value (which will be aggregated for all pages).
    :return: A list of outputs from the json_mapper function.
    """

    domain = coalesce_domain(url)
    headers = {"Authorization": f"Bearer {credentials.find_token(domain)}"}
    current_page = 1
    aggregate = []
    while current_page is not None:
        parameters = {
            # See: https://www.terraform.io/docs/cloud/api/index.html#pagination
            "page[number]": current_page,
            "page[size]": 100
        }
        response = throttle(lambda: requests.get(url, headers=headers, params=parameters))
        if response.status_code != 200:
            # yapf: disable
            print((
                f"Error reading data from {url} with parameters {parameters} - response from the "
                f"API was {response}"
            ), file=sys.stderr)
            # yapf: enable
            current_page = None
        else:
            json = response.json()
            if "data" in json:
                aggregate.append(json_mapper(json["data"]))
            current_page = _get_next_page(json)
    return aggregate
