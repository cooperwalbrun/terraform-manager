from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform.versions import group_by_version


def _ws(version: str) -> Workspace:
    return Workspace("", "", version, False)


def test_group_by_version() -> None:
    workspaces = [_ws("0.12.28"), _ws("0.13.1"), _ws("0.13.1"), _ws("0.13.5")]
    groups = group_by_version(workspaces)
    assert groups["0.13.5"] == [_ws("0.13.5")]
    assert groups["0.13.1"] == [_ws("0.13.1"), _ws("0.13.1")]
    assert groups["0.12.28"] == [_ws("0.12.28")]
