import os
import textwrap
from typing import Callable, Union, Optional
from urllib.parse import urlparse

import requests
from requests import Response
from terraform_manager.entities.error_response import ErrorResponse


def is_windows_operating_system() -> bool:  # pragma: no cover
    return os.name == "nt"


def parse_domain(url: str) -> str:
    """
    Parses the domain portion out of a URL or domain, defaulting to Terraform Cloud's domain.

    :param url: A URL corresponding to a Terraform API endpoint (either Terraform Cloud or
                Enterprise).
    :return: The domain part of the given string.
    """

    if not url.startswith("http"):
        return parse_domain(f"http://{url}")
    return urlparse(url).netloc


def get_protocol(no_tls: bool) -> str:
    return "http" if no_tls else "https"


def safe_http_request(function: Callable[[], Response]) -> Union[Response, ErrorResponse]:
    """
    Attempts to invoke a given function, catching various exceptions raised by the requests library.
    If any such exception is caught, a derived response entity is returned so that

    :param function: A function to invoke in an exception-safe context. This will commonly be an
                     HTTP request.
    :return: Either the result of invoking the given function or None.
    """

    try:
        return function()
    except requests.exceptions.RequestException as e:
        return ErrorResponse(str(e))


def wrap_text(text: str, column_limit: int) -> str:
    return os.linesep.join(textwrap.wrap(text, width=column_limit, break_long_words=False))


def is_empty(text: Optional[str]) -> bool:
    return text is None or len(text) == 0
