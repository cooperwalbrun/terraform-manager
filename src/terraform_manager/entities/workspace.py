class Workspace:
    def __init__(
        self, workspace_id: str, name: str, terraform_version: str, is_locked: bool
    ):  # pragma: no cover
        self.workspace_id = workspace_id
        self.name = name
        self.terraform_version = terraform_version
        self.is_locked = is_locked

    def __repr__(self):
        return "Workspace(workspace_id={}, name={}, terraform_version={}, is_locked={}".format(
            self.workspace_id, self.name, self.terraform_version, self.is_locked
        )

    def __str__(self):
        return self.__repr__()
