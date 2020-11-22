import sys
from argparse import ArgumentParser, Namespace
from typing import List, Optional, Dict, Any

import semver
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform import workspaces, LATEST_VERSION
from terraform_manager.terraform.locking import lock_or_unlock_workspaces
from terraform_manager.terraform.versions import group_by_version, write_version_summary, \
    patch_versions, check_versions

_parser: ArgumentParser = ArgumentParser(
    description="Manages Terraform workspaces in batch fashion."
)
operation_group = _parser.add_mutually_exclusive_group(required=True)

_parser.add_argument(
    "organization",
    type=str,
    help="The name of the organization to target within your Terraform installation (see --domain)."
)
_parser.add_argument(
    "--domain",  # We do not alias this with "-d" to avoid confusion around "-d" meaning "delete"
    type=str,
    metavar="<domain>",
    dest="domain",
    help=(
        "The domain of your Terraform Enterprise installation. If not specified, Terraform Cloud's"
        "domain will be used."
    )
)

_parser.add_argument(
    "-w",
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
_parser.add_argument(
    "-b",
    "--blacklist",
    action="store_true",
    dest="blacklist",
    help="Inverts the workspace selection criteria (see --workspaces)."
)

operation_group.add_argument(
    "--version-summary",
    action="store_true",
    dest="version_summary",
    help="Summarizes the workspaces' Terraform version information."
)
operation_group.add_argument(
    "--patch-versions",
    type=str,
    metavar="<version>",
    dest="patch_versions",
    help=(
        "Sets the workspaces' Terraform version(s) to the value provided. This can only be used to "
        "upgrade versions; downgrading is not supported due to limitations in Terraform itself. "
        "The program will stop you if the version you specify would cause a downgrade."
    )
)
operation_group.add_argument(
    "--lock",
    "--lock-workspaces",
    action="store_true",
    dest="lock_workspaces",
    help="Locks the workspaces."
)
operation_group.add_argument(
    "--unlock",
    "--unlock-workspaces",
    action="store_true",
    dest="unlock_workspaces",
    help="Unlocks the workspaces."
)


def fail() -> None:
    sys.exit(1)


def main() -> None:
    arguments: Namespace = _parser.parse_args()
    argument_dictionary: Dict[str, Any] = vars(arguments)

    organization: str = argument_dictionary["organization"]
    raw_domain: Optional[str] = argument_dictionary.get("domain")
    domain: str = "app.terraform.io" if raw_domain is None else raw_domain
    workspaces_to_target: Optional[List[str]] = argument_dictionary.get("workspaces")
    blacklist: bool = argument_dictionary["blacklist"]

    if workspaces_to_target is None and blacklist:
        # yapf: disable
        print((
            "Error: the blacklist flag is only applicable when you specify a workspace(s) to "
            "filter on."
        ), file=sys.stderr)
        # yapf: enable
        fail()

    targeted_workspaces: List[Workspace] = workspaces.fetch_all(
        domain,
        organization,
        workspaces=workspaces_to_target,
        blacklist=blacklist,
        write_error_messages=True
    )
    if len(targeted_workspaces) == 0:
        if workspaces_to_target is not None:
            names = ", ".join(workspaces_to_target)
            print(
                f'Error: no workspaces could be found with these name(s): {names}', file=sys.stderr
            )
        else:
            print("Error: no workspaces could be found in your organization.", file=sys.stderr)
        fail()
    elif argument_dictionary["version_summary"]:
        data = group_by_version(targeted_workspaces)
        write_version_summary(domain, organization, workspaces_to_target is not None, data)
    elif argument_dictionary.get("patch_versions") is not None:
        desired_version = argument_dictionary["patch_versions"]
        if not semver.VersionInfo.isvalid(desired_version) and desired_version != LATEST_VERSION:
            # yapf: disable
            print((
                f"Error: the value for patch_versions you specified ({desired_version}) is not "
                f"valid."
            ), file=sys.stderr)
            # yapf: enable
            fail()
        else:
            if not check_versions(targeted_workspaces, desired_version):
                # yapf: disable
                print((
                    "Error: at least one of the target workspaces has a version newer than the "
                    "one you are attempting to change to. No workspaces were updated."
                ), file=sys.stderr)
                # yapf: enable
                fail()
            else:
                total_success = patch_versions(
                    domain, targeted_workspaces, new_version=desired_version, write_output=True
                )
                if not total_success:
                    # There is no need to write any error messages because a report is written by
                    # the patch_versions method
                    fail()
    elif argument_dictionary["lock_workspaces"] or argument_dictionary["unlock_workspaces"]:
        total_success = lock_or_unlock_workspaces(
            domain,
            organization,
            targeted_workspaces,
            set_lock=argument_dictionary["lock_workspaces"],
            write_output=True
        )
        if not total_success:
            # There is no need to write any error messages because a report is written by
            # the lock_or_unlock_workspaces method
            fail()


if __name__ == "__main__":
    main()
