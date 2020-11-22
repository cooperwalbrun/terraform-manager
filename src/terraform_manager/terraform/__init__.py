from typing import Dict

from terraform_manager.terraform.credentials import find_token

LATEST_VERSION: str = "latest"  # The string Terraform uses when a workspace is set to auto-update


def get_api_headers(terraform_domain: str, write_error_messages: bool = False) -> Dict[str, str]:
    """
    Returns a headers dictionary needed to issue valid HTTP requests to the Terraform API (including
    authorization information).

    :param terraform_domain: The domain corresponding to a Terraform installation (either Terraform
                             Cloud or Enterprise).
    :param write_error_messages: Whether to write error messages to STDERR.
    :return: A dictionary of header key-value pairs suitable for accessing the Terraform API.
    """

    token = find_token(terraform_domain, write_error_messages=write_error_messages)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/vnd.api+json"}
