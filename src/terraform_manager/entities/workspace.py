from semver import VersionInfo


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
        self.terraform_version: VersionInfo = VersionInfo.parse(terraform_version)
        self.auto_apply = auto_apply
        self.is_locked = is_locked

    def is_terraform_version_newer_than(self, version: str) -> bool:
        return self.terraform_version.compare(version) > 0

    def is_terraform_version_older_than(self, version: str) -> bool:
        return self.terraform_version.compare(version) < 0

    def is_terraform_version_equal_to(self, version: str) -> bool:
        return self.terraform_version.compare(version) == 0

    def __repr__(self):
        return (
            f"Workspace(id={self.workspace_id}, name={self.name}, "
            f"terraform_version={str(self.terraform_version)}, auto_apply={self.auto_apply}, "
            f"is_locked={self.is_locked})"
        )

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        if isinstance(other, Workspace):
            return other.workspace_id == self.workspace_id
        else:
            return False
