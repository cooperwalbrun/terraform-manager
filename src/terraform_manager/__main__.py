import sys
from argparse import ArgumentParser, Namespace
from typing import List, Optional

import semver
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform import workspaces, LATEST_VERSION
from terraform_manager.terraform.versions import group_by_version, write_version_summary, \
    patch_versions, check_versions

_parser: ArgumentParser = ArgumentParser(
    description="Manages Terraform workspaces in batch fashion."
)
_parser.add_argument(
    "organization",
    type=str,
    help="The name of the organization to target within your Terraform installation (see --url)."
)
_parser.add_argument(
    "--domain",
    type=str,
    metavar="<domain>",
    dest="domain",
    help=(
        "The domain of your Terraform Enterprise installation. If not specified, Terraform Cloud's"
        "domain will be used."
    )
)
_parser.add_argument(
    "--version-summary",
    action="store_true",
    dest="version_summary",
    help="Summarizes the workspaces' Terraform version information."
)
_parser.add_argument(
    "--patch-versions",
    type=str,
    metavar="<version>",
    dest="patch_versions",
    help=(
        "Sets the workspaces' Terraform version(s) to the value provided. This can only be used to "
        "upgrade versions; downgrading is not supported due to limitations in Terraform itself."
    )
)
_parser.add_argument(
    "--workspaces",
    type=str,
    metavar="<workspace>",
    nargs="+",
    dest="workspaces",
    help=(
        "The names of workspace(s) to target for whichever operation is being used (if not "
        "specified, all workspaces will be automatically discovered and targeted)."
    )
)


def main() -> None:
    arguments: Namespace = _parser.parse_args()
    argument_dictionary = vars(arguments)

    organization: str = argument_dictionary["organization"]
    raw_domain: Optional[str] = argument_dictionary.get("domain")
    domain: str = "app.terraform.io" if raw_domain is None else raw_domain
    workspaces_to_target: Optional[List[str]] = argument_dictionary.get("workspaces")

    targeted_workspaces: List[Workspace] = workspaces.fetch_all(
        domain, organization, workspaces=workspaces_to_target, write_error_messages=True
    )
    if len(targeted_workspaces) == 0:
        if workspaces_to_target is not None:
            names = ", ".join(workspaces_to_target)
            print(f'No workspaces could be found with these name(s): {names}', file=sys.stderr)
        else:
            print("No workspaces could be found in your organization.", file=sys.stderr)
        sys.exit(1)
    elif argument_dictionary["version_summary"]:
        data = group_by_version(targeted_workspaces)
        write_version_summary(domain, organization, workspaces_to_target is not None, data)
    elif argument_dictionary.get("patch_versions") is not None:
        desired_version = argument_dictionary["patch_versions"]
        if not semver.VersionInfo.isvalid(desired_version) and desired_version != LATEST_VERSION:
            print(
                f"The value for patch_versions you specified ({desired_version}) is not valid.",
                file=sys.stderr
            )
            sys.exit(1)
        else:
            if not check_versions(targeted_workspaces, desired_version):
                # yapf: disable
                print((
                    "Error: at least one of the target workspaces has a version newer than the "
                    "one you are attempting to change to. No workspaces were updated."
                ), file=sys.stderr)
                # yapf: enable
                sys.exit(1)
            else:
                patch_versions(domain, targeted_workspaces, desired_version, write_output=True)


if __name__ == "__main__":
    main()
