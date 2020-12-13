import sys
from typing import Optional, List

from terraform_manager.entities.variable import Variable
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform import CLOUD_DOMAIN
from terraform_manager.terraform.locking import lock_or_unlock_workspaces
from terraform_manager.terraform.variables import configure_variables, delete_variables
from terraform_manager.terraform.workspaces import fetch_all, batch_operation, write_summary
from terraform_manager.utilities.utilities import is_empty


class Terraform:
    def __init__(
        self,
        terraform_domain: str,
        organization: str,
        *,
        workspace_names: Optional[List[str]] = None,
        blacklist: bool = False,
        no_tls: bool = False,
        token: Optional[str] = None,
        write_output: bool = False
    ):
        """
        Creates a class instance storing the configuration needed to access the Terraform API for a
        particular Terraform installation (cloud or enterprise).

        :param terraform_domain: The domain corresponding to the targeted Terraform installation
                                 (either Terraform Cloud or Enterprise).
        :param organization: The organization containing the workspaces to patch.
        :param workspace_names: The name(s) of workspace(s) for which data should be fetched. If not
                                specified, all workspace data will be fetched.
        :param blacklist: Whether to use the specified workspaces as a blacklist-style filter.
        :param no_tls: Whether to use SSL/TLS encryption when communicating with the Terraform API.
        :param token: A token suitable for authenticating against the Terraform API. If not
                      specified, a token will be searched for in the documented locations.
        :param write_output: Whether to write informational messages to STDOUT and STDERR.
        """

        self.terraform_domain = terraform_domain
        self.organization = organization
        self.workspace_names = workspace_names
        self.blacklist = blacklist
        self.no_tls = no_tls
        self.token = token
        self.write_output = write_output

        self._options_hash: int = self._compute_options_hash()
        self._workspace_cache: Optional[List[Workspace]] = None

    def configuration_is_valid(self) -> bool:
        """
        Checks the configuration with which this Terraform instance was created for validity.

        :return: Whether the configuration is valid.
        """

        if self.terraform_domain == CLOUD_DOMAIN and self.no_tls:
            if self.write_output:
                print(
                    "Error: you should not disable SSL/TLS when interacting with Terraform Cloud.",
                    file=sys.stderr
                )
            return False
        elif (self.workspace_names is None or len(self.workspace_names) == 0) and self.blacklist:
            if self.write_output:
                # yapf: disable
                print((
                    "Error: the blacklist flag is only applicable when you specify workspace(s) to "
                    "filter on."
                ), file=sys.stderr)
                # yapf: enable
            return False
        else:
            return True

    def _compute_options_hash(self) -> int:
        # We only compute the hash of options that influence which workspaces are returned by the
        # workspace fetch
        value = hash(self.terraform_domain) + hash(self.organization) + hash(self.blacklist) + \
                hash(self.no_tls)
        if self.workspace_names is not None:
            value += hash(tuple(self.workspace_names))
        if self.token is not None:
            value += hash(self.token)
        return value

    @property
    def workspaces(self) -> List[Workspace]:
        """
        Fetch all workspaces (or a subset if desired) from a particular Terraform organization. The
        workspaces will be fetched on a as-needed basis; they will be cached so this property
        computes in constant-time on subsequent accesses. If configuration options are updated on
        this Terraform class instance, the workspaces will be re-fetched the next time this property
        is accessed.

        :return: The fetched workspaces, if any. If the configuration in this Terraform instance is
                 not valid, an empty list will be returned.
        """

        if self._workspace_cache is None or self._options_hash != self._compute_options_hash():
            if not self.configuration_is_valid():
                return []
            self._options_hash = self._compute_options_hash()
            self._workspace_cache = fetch_all(
                self.terraform_domain,
                self.organization,
                workspace_names=self.workspace_names,
                blacklist=self.blacklist,
                token=self.token,
                write_error_messages=self.write_output
            )
        return self._workspace_cache

    def lock_workspaces(self) -> bool:
        """
        Locks the workspaces.

        :return: Whether all lock operations were successful. If even a single one failed, returns
                 False.
        """
        return lock_or_unlock_workspaces(
            self.terraform_domain,
            self.organization,
            self.workspaces,
            set_lock=True,
            no_tls=self.no_tls,
            token=self.token,
            write_output=self.write_output
        )

    def unlock_workspaces(self) -> bool:
        """
        Unlocks the workspaces.

        :return: Whether all unlock operations were successful. If even a single one failed, returns
                 False.
        """
        return lock_or_unlock_workspaces(
            self.terraform_domain,
            self.organization,
            self.workspaces,
            set_lock=False,
            no_tls=self.no_tls,
            token=self.token,
            write_output=self.write_output
        )

    def check_versions(self, new_version: str) -> bool:
        """
        Asserts whether at least one of the workspaces would be downgraded by a patch operation
        involving a given version - this is prophylactic as Terraform itself does not support
        downgrades.

        :param new_version: The new Terraform version to check against the workspaces' versions.
        :return: Whether there are any workspaces which would be downgraded by patching to the new
                 version.
        """

        for workspace in self.workspaces:
            if workspace.is_terraform_version_newer_than(new_version):
                return False
        return True

    def set_versions(self, new_version: str) -> bool:
        """
        Patches the Terraform version of the workspaces.

        :param new_version: The new Terraform version to assign to the workspaces.
        :return: Whether all patch operations were successful. If even a single one failed, returns
                 False.
        """
        if not self.check_versions(new_version):
            if self.write_output:
                # yapf: disable
                print((
                    "Error: at least one of the target workspaces has a version newer than the one "
                    "you are attempting to change to. No workspaces were updated."
                ), file=sys.stderr)
                # yapf: enable
            return False
        else:
            return batch_operation(
                self.terraform_domain,
                self.organization,
                self.workspaces,
                field_mapper=lambda w: w.terraform_version,
                field_name="terraform-version",
                new_value=new_version,
                no_tls=self.no_tls,
                token=self.token,
                write_output=self.write_output
            )

    def write_summary(self) -> None:
        """
        Writes a tabulated summary of the workspaces' configuration to STDOUT. Only values in scope
        for terraform-manager will be written. Long lines will be wrapped automatically.

        :return: None
        """
        write_summary(
            self.terraform_domain,
            self.organization,
            self.workspaces,
            targeting_specific_workspaces=self.workspace_names is not None,
            write_output=self.write_output
        )

    def set_working_directories(self, new_working_directory: Optional[str]) -> bool:
        """
        Patches the working directories of the workspaces.

        :param new_working_directory: The new working directory to assign to the workspaces.
        :return: Whether all patch operations were successful. If even a single one failed, returns
                 False.
        """
        return batch_operation(
            self.terraform_domain,
            self.organization,
            self.workspaces,
            field_mapper=lambda w: w.working_directory,
            field_name="working-directory",
            new_value="" if new_working_directory is None else new_working_directory,
            report_only_value_mapper=lambda w: "<none>" if is_empty(w) else w,
            no_tls=self.no_tls,
            token=self.token,
            write_output=self.write_output
        )

    def set_execution_modes(self, new_execution_mode: str) -> bool:
        """
        Patches the execution modes of the workspaces.

        :param new_execution_mode: The new execution mode to assign to the workspaces. The value
                                   must be either "remote", "local", or "agent" (case-sensitive).
        :return: Whether all patch operations were successful. If even a single one failed, returns
                 False.
        """
        if new_execution_mode not in ["remote", "local", "agent"]:
            if self.write_output:
                print(
                    f"Error: invalid execution-mode specified: {new_execution_mode}",
                    file=sys.stderr
                )
            return False
        else:
            return batch_operation(
                self.terraform_domain,
                self.organization,
                self.workspaces,
                field_mapper=lambda w: w.execution_mode,
                field_name="execution-mode",
                new_value=new_execution_mode,
                no_tls=self.no_tls,
                token=self.token,
                write_output=self.write_output
            )

    def set_auto_apply(self, set_auto_apply: bool) -> bool:
        """
        Patches the auto-apply setting of the workspaces.

        :param set_auto_apply: The desired value of the workspaces' auto-apply setting.
        :return: Whether all patch operations were successful. If even a single one failed, returns
                 False.
        """
        return batch_operation(
            self.terraform_domain,
            self.organization,
            self.workspaces,
            field_mapper=lambda w: w.auto_apply,
            field_name="auto-apply",
            new_value=set_auto_apply,
            no_tls=self.no_tls,
            token=self.token,
            write_output=self.write_output
        )

    def set_speculative(self, set_speculative: bool) -> bool:
        """
        Patches the speculative-enabled setting of the workspaces.

        :param set_speculative: The desired value of the workspaces' speculative-enabled setting.
        :return: Whether all patch operations were successful. If even a single one failed, returns
                 False.
        """
        return batch_operation(
            self.terraform_domain,
            self.organization,
            self.workspaces,
            field_mapper=lambda w: w.speculative,
            field_name="speculative-enabled",
            new_value=set_speculative,
            no_tls=self.no_tls,
            token=self.token,
            write_output=self.write_output
        )

    def delete_variables(self, variables: List[str]) -> bool:
        """
        Deletes one or more variables for the workspaces. If a variable does not exist in a
        particular workspace, no operation is performed relative to that variable (this is a safe
        operation). This behavior allows this method to be idempotent.

        :param variables: The keys of the variables to delete.
        :return: Whether all HTTP operations were successful. If even a single one failed, returns
                 False.
        """
        return delete_variables(
            self.terraform_domain,
            self.organization,
            self.workspaces,
            variables=variables,
            no_tls=self.no_tls,
            token=self.token,
            write_output=self.write_output
        )

    def configure_variables(self, variables: List[Variable]) -> bool:
        """
        Creates or updates (in-place) one or more variables for the workspaces. If variables already
        exist with same keys, they will instead be updated so that all their fields equal the ones
        given in the variables passed to this method. This behavior allows this method to be
        idempotent.

        :param variables: The variables to either create or update.
        :return: Whether all HTTP operations were successful. If even a single one failed, returns
                 False.
        """
        return configure_variables(
            self.terraform_domain,
            self.organization,
            self.workspaces,
            variables=variables,
            no_tls=self.no_tls,
            token=self.token,
            write_output=self.write_output
        )

    def __repr__(self):
        return (
            "Terraform(domain={}, organization={}, workspaces=List[{}], blacklist={}, no_tls={}, "
            "token={}, write_output={})"
        ).format(
            self.terraform_domain,
            self.organization,
            len(self.workspaces),
            self.blacklist,
            self.no_tls,
            "<REDACTED>" if self.token is not None else "None",
            self.write_output
        )

    def __str__(self):
        return repr(self)
