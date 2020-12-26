import calendar
import os
import textwrap
import time
from datetime import datetime, timezone
from typing import Callable, Union, Optional, Dict, Any, List
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


def coalesce(text: Optional[str], default: str) -> str:
    return default if is_empty(text) else text


def safe_deep_get(dictionary: Dict[str, Any], path: List[str]) -> Optional[Any]:
    if len(path) > 0:
        m = dictionary
        for i in range(len(path) - 1):
            if isinstance(m, dict):
                m = m.get(path[i], {})
                if m is None:
                    m = {}
            else:
                return None
        if isinstance(m, dict):
            return m.get(path[-1])
        else:
            return None
    else:
        return None


def convert_timestamp_to_unix_time(timestamp: str, timestamp_format: str) -> Optional[int]:
    # Python 3 reference for the possible flags for datetime.strptime():
    # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
    try:
        parsed_datetime = datetime.strptime(timestamp, timestamp_format)
        if parsed_datetime.tzinfo is None:
            # We assume the time is in UTC if no zone information was available/parsed
            parsed_datetime = parsed_datetime.replace(tzinfo=timezone.utc)
        return round(parsed_datetime.timestamp())
    except:
        return None


def convert_hashicorp_timestamp_to_unix_time(timestamp: str) -> Optional[int]:
    if "+" in timestamp:
        # The following steps transform the +HH:MM format that HashiCorp returns into +HHMM in order
        # for the string to work with the %z flag used with datetime.strptime()
        parts = timestamp.split("+")
        reformatted_zone = parts[1].replace(":", "")
        fixed_form = parts[0] + "+" + reformatted_zone
        return convert_timestamp_to_unix_time(fixed_form, "%Y-%m-%dT%H:%M:%S%z")
    else:
        return None
