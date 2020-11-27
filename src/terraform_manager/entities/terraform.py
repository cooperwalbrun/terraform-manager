from typing import Optional, List

from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform.locking import lock_or_unlock_workspaces
from terraform_manager.terraform.versions import check_versions, patch_versions, \
    write_version_summary, group_by_version
from terraform_manager.terraform.working_directories import patch_working_directories
from terraform_manager.terraform.workspaces import fetch_all


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
        self.terraform_domain = terraform_domain
        self.organization = organization
        self.workspace_names = workspace_names
        self.blacklist = blacklist
        self.no_tls = no_tls
        self.token = token
        self.write_output = write_output

        self._options_hash: int = self._compute_options_hash()
        self._workspace_cache: Optional[List[Workspace]] = None

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

        :return: The fetched workspaces, if any.
        """
        if self._workspace_cache is None or self._options_hash != self._compute_options_hash():
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
        return check_versions(self.workspaces, new_version)

    def patch_versions(self, new_version: str) -> bool:
        """
        Patches the Terraform version of the workspaces.

        :param new_version: The new Terraform version to assign to the workspaces.
        :return: Whether all patch operations were successful. If even a single one failed, returns
                 False.
        """
        return patch_versions(
            self.terraform_domain,
            self.organization,
            self.workspaces,
            new_version=new_version,
            no_tls=self.no_tls,
            token=self.token,
            write_output=self.write_output
        )

    def write_version_summary(self) -> None:
        """
        Writes a tabulated summary of the workspaces and their versions to STDOUT. Long lines will
        be wrapped automatically.

        :return: None
        """
        write_version_summary(
            self.terraform_domain,
            self.organization,
            self.workspace_names is not None,
            group_by_version(self.workspaces)
        )

    def set_working_directories(self, new_working_directory: Optional[str]) -> bool:
        """
        Patches the working directories of the workspaces.

        :param new_working_directory: The new working directory to assign to the workspaces.
        :return: Whether all patch operations were successful. If even a single one failed, returns
                 False.
        """
        return patch_working_directories(
            self.terraform_domain,
            self.organization,
            self.workspaces,
            new_working_directory=new_working_directory,
            no_tls=self.no_tls,
            write_output=self.write_output
        )

    def __repr__(self):
        return (
            "Terraform(domain={}, organization={}, workspaces=List[{}], blacklist={}, "
            "no_tls={}, token={}, write_output={})"
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
