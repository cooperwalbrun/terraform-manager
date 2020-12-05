import sys
from argparse import ArgumentParser, Namespace
from typing import List, Optional, Dict, Any

from terraform_manager import cli_handlers
from terraform_manager.entities.terraform import Terraform
from terraform_manager.terraform import CLOUD_DOMAIN

_parser: ArgumentParser = ArgumentParser(
    description="Manages Terraform workspaces in batch fashion."
)
_selection_group = _parser.add_argument_group()
_operation_group = _selection_group.add_mutually_exclusive_group(required=False)
_special_group = _parser.add_mutually_exclusive_group(required=False)

_selection_group.add_argument(
    "-o",
    "--organization",
    type=str,
    metavar="ORGANIZATION",
    dest="organization",
    help="The name of the organization to target within your Terraform installation (see --domain)."
)
_selection_group.add_argument(
    "--domain",  # We do not alias this with "-d" to avoid confusion around "-d" meaning "delete"
    type=str,
    metavar="DOMAIN",
    dest="domain",
    help=(
        "The domain of your Terraform Enterprise installation. If not specified, Terraform Cloud's "
        "domain will be used."
    )
)
_selection_group.add_argument(
    "--no-tls",
    "--no-ssl",
    action="store_true",
    dest="no_tls",
    help=(
        "NOT RECOMMENDED. Disables HTTPS interactions with the Terraform API in favor of HTTP. "
        "This option should only be used when targeting a Terraform Enterprise installation that "
        "does not have SSL/TLS enabled."
    )
)
_selection_group.add_argument(
    "-w",
    "--workspaces",
    type=str,
    metavar="WORKSPACE",
    nargs="+",
    dest="workspaces",
    help=(
        "The names of workspace(s) to target for whichever operation is being used (if not "
        "specified, all workspaces will be automatically discovered and targeted)."
    )
)
_selection_group.add_argument(
    "-b",
    "--blacklist",
    action="store_true",
    dest="blacklist",
    help="Inverts the workspace selection criteria (see --workspaces)."
)

_operation_group.add_argument(
    "--version-summary",
    action="store_true",
    dest="version_summary",
    help="Summarizes the workspaces' Terraform version information."
)
_operation_group.add_argument(
    "--patch-versions",
    type=str,
    metavar="VERSION",
    dest="patch_versions",
    help=(
        "Sets the workspaces' Terraform versions to the value provided. This can only be used to "
        "upgrade versions; downgrading is not supported due to limitations in Terraform itself. "
        "The program will stop you if the version you specify would cause a downgrade."
    )
)
_operation_group.add_argument(
    "--lock",
    "--lock-workspaces",
    action="store_true",
    dest="lock_workspaces",
    help="Locks the workspaces."
)
_operation_group.add_argument(
    "--unlock",
    "--unlock-workspaces",
    action="store_true",
    dest="unlock_workspaces",
    help="Unlocks the workspaces."
)
_operation_group.add_argument(
    "--working-dir",
    type=str,
    metavar="DIRECTORY",
    dest="working_directory",
    help="Sets the workspaces' working directories to the value provided."
)
_operation_group.add_argument(
    "--clear-working-dir",
    action="store_true",
    dest="clear_working_directory",
    help="Clears the workspaces' working directories."
)
_operation_group.add_argument(
    "--configure-vars",
    type=str,
    metavar="FILE",
    dest="configure_variables",
    help=(
        "Creates/updates the variables specified in the given file in the workspaces. See also "
        "--create-vars-template."
    )
)
_operation_group.add_argument(
    "--delete-vars",
    type=str,
    metavar="KEY",
    nargs="+",
    dest="delete_variables",
    help="Deletes the variables specified by-key in the workspaces."
)

_special_group.add_argument(
    "--create-vars-template",
    action="store_true",
    dest="create_variables_template",
    help=(
        "Creates a template JSON file suitable for configuring variables via the --configure-vars "
        "flag in the current directory."
    )
)


def _get_arguments() -> List[str]:  # pragma: no cover
    # This logic is extracted into its own method for unit test mocking purposes
    return sys.argv[1:]


def _parse_arguments(arguments: List[str]) -> Dict[str, Any]:
    arguments: Namespace = _parser.parse_args(arguments)
    return vars(arguments)


def _get_selection_argument(arguments: List[str]) -> Optional[str]:  # pragma: no cover
    flags = [
        "-o",
        "--organization",
        "--domain",
        "--no-tls",
        "--no-ssl"
        "-w",
        "--workspaces",
        "-b",
        "--blacklist"
    ]
    for flag in flags:
        if flag in arguments:
            return flag
    return None


def _get_special_argument(arguments: List[str]) -> Optional[str]:  # pragma: no cover
    flags = ["--create-vars-template"]
    for flag in flags:
        if flag in arguments:
            return flag
    return None


def _no_selection_arguments_main(arguments: Dict[str, Any]) -> None:
    if arguments["create_variables_template"]:
        cli_handlers.create_variables_template()


def _organization_required_main(arguments: Dict[str, Any]) -> None:
    organization: str = arguments["organization"]
    if arguments.get("domain") is None:
        domain: str = CLOUD_DOMAIN
    else:
        domain: str = arguments["domain"].lower()
    workspaces_to_target: Optional[List[str]] = arguments.get("workspaces")
    blacklist: bool = arguments["blacklist"]
    no_tls: bool = arguments["no_tls"]

    terraform: Terraform = Terraform(
        domain,
        organization,
        workspace_names=workspaces_to_target,
        blacklist=blacklist,
        no_tls=no_tls,
        token=None,  # We disallow specifying a token inline at the CLI for security reasons
        write_output=True
    )
    if not terraform.configuration_is_valid() or not cli_handlers.validate(terraform):
        cli_handlers.fail()
    elif arguments["version_summary"]:
        terraform.write_version_summary()
    elif arguments.get("patch_versions") is not None:
        cli_handlers.patch_versions(terraform, arguments["patch_versions"])
    elif arguments["lock_workspaces"] or arguments["unlock_workspaces"]:
        cli_handlers.lock_or_unlock_workspaces(terraform, arguments["lock_workspaces"])
    elif arguments.get("working_directory") is not None or arguments["clear_working_directory"]:
        cli_handlers.set_working_directories(terraform, arguments.get("working_directory"))
    elif arguments.get("configure_variables") is not None:
        cli_handlers.configure_variables(terraform, arguments["configure_variables"])
    elif arguments.get("delete_variables") is not None:
        cli_handlers.delete_variables(terraform, arguments["delete_variables"])
    else:
        _parser.error("Unable to determine which operation you are attempting to perform.")


def main() -> None:
    args = _get_arguments()

    if len(args) == 0:
        _parser.error("You must specify at least one argument.")
    elif _get_selection_argument(args) is not None and _get_special_argument(args) is not None:
        _parser.error((
            f"You cannot specify any selection arguments (such as {_get_selection_argument(args)}) "
            f"at the same time as {_get_special_argument(args)}."
        ))
    else:
        arguments = _parse_arguments(args)
        if arguments["create_variables_template"]:
            _no_selection_arguments_main(arguments)
        elif "organization" not in arguments:
            _parser.error("You must specify an organization to target.")
        else:
            _organization_required_main(arguments)


if __name__ == "__main__":
    main()
