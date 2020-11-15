import json
import os
import sys
from typing import Optional, List, Any

from terraform_manager.utilities import utilities

_token_environment_variable_name = "TERRAFORM_TOKEN"
_windows_credentials_locations: List[str] = [
    "$APPDATA/terraform.d/credentials.tfrc.json",
    "$TF_CLI_CONFIG_FILE"  # See: https://www.terraform.io/docs/commands/cli-config.html
]
_unix_credentials_locations: List[str] = [
    "$HOME/.terraform.d/credentials.tfrc.json",
    "$TF_CLI_CONFIG_FILE"  # See: https://www.terraform.io/docs/commands/cli-config.html
]
_cached_token: Optional[str] = None


def _parse_json_for_token(domain: str, credentials_json: Any) -> Optional[str]:
    if credentials_json is not None and "credentials" in credentials_json and domain in \
            credentials_json["credentials"]:
        return credentials_json["credentials"][domain].get("token")
    return None


def find_token(terraform_domain: str) -> Optional[str]:
    """
    Searches for a token to use for Terraform API invocations in three places: first, the
    TERRAFORM_TOKEN environment variable; second, the credentials JSON file that Terraform itself
    creates and uses for CLI operations; third, the TF_CLI_CONFIG_FILE environment variable. The
    latter two approaches are documented by HashiCorp here:
    https://www.terraform.io/docs/commands/cli-config.html.

    :param terraform_domain: The domain component of the API endpoint which you require an access
                             token for.
    :return: The access token if one can be found.
    """

    global _cached_token
    if _cached_token is not None:
        return _cached_token
    credentials_json = None
    if os.environ.get(_token_environment_variable_name) is not None:
        _cached_token = os.environ[_token_environment_variable_name]
        return _cached_token
    if utilities.is_windows_operating_system():
        paths = _windows_credentials_locations
    else:
        paths = _unix_credentials_locations
    for path in paths:
        expanded_path = os.path.expandvars(path)
        if os.path.exists(expanded_path):
            try:
                with open(expanded_path) as file:
                    credentials_json = json.load(file)
                break
            except:
                # yapf: disable
                print((
                    f"Error: a credentials file was found at {expanded_path}, but valid JSON could "
                    "not be parsed from it."
                ), file=sys.stderr)
                # yapf: enable
    _cached_token = _parse_json_for_token(terraform_domain, credentials_json)
    return _cached_token
