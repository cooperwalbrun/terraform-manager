from typing import Optional

from semver import VersionInfo
from terraform_manager.terraform import LATEST_VERSION


class Workspace:
    def __init__(
        self,
        workspace_id: str,
        name: str,
        terraform_version: str,
        auto_apply: bool,
        is_locked: bool
    ):  # pragma: no cover
        self.workspace_id = workspace_id
        self.name = name

        self.terraform_version = terraform_version
        self.parsed_terraform_version: Optional[VersionInfo] = None
        if VersionInfo.isvalid(terraform_version):
            self.parsed_terraform_version: VersionInfo = VersionInfo.parse(terraform_version)
        self.is_auto_updating: bool = self.terraform_version == LATEST_VERSION

        self.auto_apply = auto_apply
        self.is_locked = is_locked

    def is_terraform_version_newer_than(self, version: str) -> bool:
        if self.terraform_version == LATEST_VERSION:
            return version != LATEST_VERSION
        else:
            return version != LATEST_VERSION and self.parsed_terraform_version.compare(version) > 0

    def is_terraform_version_older_than(self, version: str) -> bool:
        if self.terraform_version == LATEST_VERSION:
            return False
        else:
            return version == LATEST_VERSION or self.parsed_terraform_version.compare(version) < 0

    def is_terraform_version_equal_to(self, version: str) -> bool:
        return self.terraform_version == version

    def __repr__(self):
        return (
            f"Workspace(id={self.workspace_id}, name={self.name}, "
            f"terraform_version={self.terraform_version}, auto_apply={self.auto_apply}, "
            f"is_locked={self.is_locked})"
        )

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        if isinstance(other, Workspace):
            return other.workspace_id == self.workspace_id
        else:
            return False
