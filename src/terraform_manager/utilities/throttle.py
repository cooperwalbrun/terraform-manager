from typing import Callable

from ratelimit import limits, sleep_and_retry
from requests import Response


@sleep_and_retry
@limits(calls=30, period=1)
def throttle(function: Callable[[], Response]) -> Response:
    """
    Throttles an operation based on Terraform's documented API rate limits. If the operation would
    breach the rate limit, it will block on the current thread until it is safe to execute.

    See: https://www.terraform.io/docs/cloud/api/index.html#rate-limiting for more information.

    :param function: A function to invoke while throttling. This will commonly be an HTTP request.
    :return: The result of the function, if any.
    """

    return function()
