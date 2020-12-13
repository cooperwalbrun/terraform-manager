from typing import Dict, Optional, TypeVar, Callable, Union

from requests import Response
from terraform_manager.entities.error_response import ErrorResponse
from terraform_manager.terraform.credentials import find_token

CLOUD_DOMAIN: str = "app.terraform.io"
LATEST_VERSION: str = "latest"  # The string Terraform uses when a workspace is set to auto-update
HTTP_CONTENT_TYPE: str = "application/vnd.api+json"

MESSAGE_COLUMN_CHARACTER_COUNT: int = 70

A = TypeVar("A")
SuccessHandler = Callable[[A], None]
ErrorHandler = Callable[[A, Union[Response, ErrorResponse]], None]


def get_api_headers(
    terraform_domain: str,
    *,
    token: Optional[str] = None,
    write_error_messages: bool = False
) -> Dict[str, str]:
    """
    Returns a headers dictionary needed to issue valid HTTP requests to the Terraform API (including
    authorization information).

    :param terraform_domain: The domain corresponding to a Terraform installation (either Terraform
                             Cloud or Enterprise).
    :param token: A token suitable for authenticating against the Terraform API. If not specified, a
                  token will be searched for in the documented locations.
    :param write_error_messages: Whether to write error messages to STDERR.
    :return: A dictionary of header key-value pairs suitable for accessing the Terraform API.
    """

    if token is None:
        found_token = find_token(terraform_domain, write_error_messages=write_error_messages)
        if found_token is None:
            return {"Content-Type": HTTP_CONTENT_TYPE}
        else:
            return {"Authorization": f"Bearer {found_token}", "Content-Type": HTTP_CONTENT_TYPE}
    else:
        return {"Authorization": f"Bearer {token}", "Content-Type": HTTP_CONTENT_TYPE}
