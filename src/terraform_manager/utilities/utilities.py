import os
from typing import Optional, Callable, Union
from urllib.parse import urlparse

import requests
from requests import Response
from terraform_manager.entities.error_response import ErrorResponse


def is_windows_operating_system() -> bool:  # pragma: no cover
    return os.name == "nt"


def coalesce_domain(url_or_domain: Optional[str]) -> str:
    """
    Parses the domain portion out of a URL or domain, defaulting to Terraform Cloud's domain.

    :param url_or_domain: The URL (or just the domain part of a URL) corresponding to a Terraform
                          API endpoint (either Terraform Cloud or Enterprise).
    :return: The domain part of the given string, or Terraform Cloud's domain if no URL/domain was
             provided.
    """

    if url_or_domain is not None and not url_or_domain.startswith("http"):
        return coalesce_domain(f"http://{url_or_domain}")
    return "app.terraform.io" if url_or_domain is None else urlparse(url_or_domain).netloc


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
