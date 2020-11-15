from argparse import ArgumentParser, Namespace
from typing import Dict, Union

from terraform_manager.terraform import workspaces
from terraform_manager.terraform.versions import group_by_version

_parser: ArgumentParser = ArgumentParser(
    description="Manages Terraform workspaces in batch fashion."
)
_parser.add_argument(
    "organization",
    type=str,
    help="The name of the organization to target within your Terraform installation"
)
_parser.add_argument(
    "--url",
    type=str,
    metavar="<url>",
    dest="url",
    help=(
        "The URL of your Terraform Enterprise installation. If not specified, Terraform Cloud will "
        "be used."
    )
)
_parser.add_argument(
    "--list-versions",
    action="store_true",
    dest="list_versions",
    help="Lists the organization's workspaces' Terraform version(s) to the value provided"
)
_parser.add_argument(
    "--set-version",
    type=str,
    metavar="<version>",
    dest="set_version",
    help="Sets the organization's workspaces' Terraform version(s) to the value provided"
)
_parser.add_argument(
    "--workspaces",
    type=str,
    metavar="<workspace>",
    nargs="+",
    dest="workspaces",
    help=(
        "The names of workspace(s) to target for whichever operation(s) are being used (if not "
        "specified, all workspaces will be discovered and targeted)"
    )
)


def main() -> None:
    arguments: Namespace = _parser.parse_args()
    argument_dictionary: Dict[str, Union[str, bool]] = vars(arguments)
    targeted_workspaces = workspaces.fetch_all(
        argument_dictionary["organization"],
        workspaces=argument_dictionary.get("workspaces"),
        url=argument_dictionary.get("url")
    )
    print(group_by_version(targeted_workspaces))


if __name__ == "__main__":
    main()
