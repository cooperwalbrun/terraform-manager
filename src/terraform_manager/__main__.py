import sys
from argparse import ArgumentParser, Namespace
from typing import List, Optional

from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform import workspaces
from terraform_manager.terraform.versions import group_by_version, write_version_summary

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
        "The URL or domain of your Terraform Enterprise installation. If not specified, Terraform "
        "Cloud will be used."
    )
)
_parser.add_argument(
    "--version-summary",
    action="store_true",
    dest="version_summary",
    help="Summarizes the workspaces' Terraform version information"
)
_parser.add_argument(
    "--set-version",
    type=str,
    metavar="<version>",
    dest="set_version",
    help="Sets the workspaces' Terraform version(s) to the value provided"
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
    argument_dictionary = vars(arguments)

    organization: str = argument_dictionary["organization"]
    url: Optional[str] = argument_dictionary.get("url")
    workspaces_to_target: Optional[List[str]] = argument_dictionary.get("workspaces")

    targeted_workspaces: List[Workspace] = workspaces.fetch_all(
        organization, workspaces=workspaces_to_target, url=url
    )
    if len(targeted_workspaces) == 0:
        print(
            f'No workspaces could be found with these name(s): {", ".join(workspaces_to_target)}',
            file=sys.stderr
        )
        sys.exit(1)
    elif argument_dictionary["version_summary"]:
        data = group_by_version(targeted_workspaces)
        write_version_summary(organization, workspaces_to_target is not None, url, data)


if __name__ == "__main__":
    main()
