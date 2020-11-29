import sys
from argparse import ArgumentParser, Namespace
from typing import List, Optional, Dict, Any

import semver
from terraform_manager.entities.terraform import Terraform
from terraform_manager.terraform import LATEST_VERSION
from terraform_manager.terraform.variables import create_variables_template, parse_variables

_parser: ArgumentParser = ArgumentParser(
    description="Manages Terraform workspaces in batch fashion."
)
operation_group = _parser.add_mutually_exclusive_group(required=True)

_parser.add_argument(
    "-o",
    "--organization",
    type=str,
    metavar="<organization>",
    dest="organization",
    help="The name of the organization to target within your Terraform installation (see --domain)."
)
_parser.add_argument(
    "--domain",  # We do not alias this with "-d" to avoid confusion around "-d" meaning "delete"
    type=str,
    metavar="<domain>",
    dest="domain",
    help=(
        "The domain of your Terraform Enterprise installation. If not specified, Terraform Cloud's "
        "domain will be used."
    )
)
_parser.add_argument(
    "--no-ssl",
    "--no-tls",
    action="store_true",
    dest="no_tls",
    help=(
        "NOT RECOMMENDED. Disables HTTPS interactions with the Terraform API in favor of HTTP. "
        "This option should only be used when targeting a Terraform Enterprise installation that "
        "does not have SSL/TLS enabled."
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
        "Sets the workspaces' Terraform versions to the value provided. This can only be used to "
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
operation_group.add_argument(
    "--working-dir",
    type=str,
    metavar="<directory>",
    dest="working_directory",
    help="Sets the workspaces' working directories to the value provided."
)
operation_group.add_argument(
    "--clear-working-dir",
    action="store_true",
    dest="clear_working_directory",
    help="Clears the workspaces' working directories."
)
operation_group.add_argument(
    "--create-vars-template",
    action="store_true",
    dest="create_variables_template",
    help=(
        "Creates a template JSON file suitable for configuring variables via the --configure-vars "
        "flag in the current directory."
    )
)
operation_group.add_argument(
    "--configure-vars",
    type=str,
    metavar="<variables file>",
    dest="configure_variables",
    help=(
        "Creates/updates the variables specified in the given file in the workspaces. See "
        "--create-vars-template."
    )
)


def parse_arguments(arguments: List[str]) -> Dict[str, Any]:
    arguments: Namespace = _parser.parse_args(arguments)
    return vars(arguments)


def fail() -> None:
    sys.exit(1)


def no_required_arguments_main(argument_dictionary: Dict[str, Any]) -> None:
    if argument_dictionary["create_variables_template"]:
        success = create_variables_template(write_output=True)
        if not success:
            # There is no need to write any error messages because they will be written by the
            # create_variables_template method
            fail()


def organization_required_main(argument_dictionary: Dict[str, Any]) -> None:
    organization: str = argument_dictionary["organization"]
    raw_domain: Optional[str] = argument_dictionary.get("domain")
    domain: str = "app.terraform.io" if raw_domain is None else raw_domain.lower()
    workspaces_to_target: Optional[List[str]] = argument_dictionary.get("workspaces")
    blacklist: bool = argument_dictionary["blacklist"]
    no_tls: bool = argument_dictionary["no_tls"]

    if domain == "app.terraform.io" and no_tls:
        print(
            "Error: you should never disable SSL/TLS when interacting with Terraform Cloud.",
            file=sys.stderr
        )
        fail()
    elif workspaces_to_target is None and blacklist:
        # yapf: disable
        print((
            "Error: the blacklist flag is only applicable when you specify a workspace(s) to "
            "filter on."
        ), file=sys.stderr)
        # yapf: enable
        fail()
    else:
        terraform: Terraform = Terraform(
            domain,
            organization,
            workspace_names=workspaces_to_target,
            blacklist=blacklist,
            no_tls=no_tls,
            token=None,  # We disallow specifying a token inline at the CLI for security reasons
            write_output=True
        )
        if len(terraform.workspaces) == 0:
            if workspaces_to_target is not None:
                names = ", ".join(workspaces_to_target)
                print(
                    f"Error: no workspaces could be found with these name(s): {names}",
                    file=sys.stderr
                )
            else:
                print("Error: no workspaces could be found in your organization.", file=sys.stderr)
            fail()
        elif argument_dictionary["version_summary"]:
            terraform.write_version_summary()
        elif argument_dictionary.get("patch_versions") is not None:
            desired_version = argument_dictionary["patch_versions"]
            if not semver.VersionInfo.isvalid(desired_version) and \
                    desired_version != LATEST_VERSION:
                # yapf: disable
                print((
                    f"Error: the value for patch_versions you specified ({desired_version}) is not "
                    "valid."
                ), file=sys.stderr)
                # yapf: enable
                fail()
            elif not terraform.check_versions(desired_version):
                # yapf: disable
                print((
                    "Error: at least one of the target workspaces has a version newer than the one "
                    "you are attempting to change to. No workspaces were updated."
                ), file=sys.stderr)
                # yapf: enable
                fail()
            else:
                total_success = terraform.patch_versions(desired_version)
                if not total_success:
                    # There is no need to write any error messages because a report is written by
                    # the patch_versions method
                    fail()
        elif argument_dictionary["lock_workspaces"] or argument_dictionary["unlock_workspaces"]:
            if argument_dictionary["lock_workspaces"]:
                total_success = terraform.lock_workspaces()
            else:
                total_success = terraform.unlock_workspaces()
            if not total_success:
                # There is no need to write any error messages because a report is written by the
                # lock_or_unlock_workspaces method
                fail()
        elif argument_dictionary.get("working_directory") is not None or \
                argument_dictionary["clear_working_directory"]:
            total_success = terraform.set_working_directories(
                argument_dictionary.get("working_directory")
            )
            if not total_success:
                # There is no need to write any error messages because a report is written by the
                # patch_working_directories method
                fail()
        elif argument_dictionary.get("configure_variables") is not None:
            file = argument_dictionary["configure_variables"]
            variables = parse_variables(file, write_output=True)
            if len(variables) == 0:
                print(f"Error: no variable definitions found in {file}.", file=sys.stderr)
                fail()
            else:
                total_success = terraform.configure_variables(variables)
                if not total_success:
                    # There is no need to write any error messages because a report is written by
                    # the configure_variables method
                    fail()
        # We do not have to have an "else" because argparse should make fallthrough impossible


def main() -> None:
    argument_dictionary = parse_arguments(sys.argv[1:])

    if argument_dictionary["create_variables_template"]:
        no_required_arguments_main(argument_dictionary)
    elif "organization" not in argument_dictionary:
        print("Error: you must specify an organization to target.", file=sys.stderr)
        fail()
    else:
        organization_required_main(argument_dictionary)


if __name__ == "__main__":
    main()
