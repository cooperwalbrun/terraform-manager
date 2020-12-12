from terraform_manager.entities.workspace import Workspace

from tests.utilities.tooling import test_workspace


def test_version_comparisons() -> None:
    workspace1 = test_workspace(version="0.12.28")
    workspace2 = test_workspace(version="0.13.1")
    workspace3 = test_workspace(version="0.13.1")
    workspace4 = test_workspace(version="latest")
    workspace5 = test_workspace(version="latest")
    assert workspace2.is_terraform_version_newer_than(workspace1.terraform_version)
    assert workspace1.is_terraform_version_older_than(workspace2.terraform_version)
    assert workspace2.is_terraform_version_equal_to(workspace3.terraform_version)
    assert workspace4.is_terraform_version_equal_to(workspace5.terraform_version)
    assert workspace5.is_terraform_version_equal_to(workspace4.terraform_version)
    assert not workspace1.is_terraform_version_newer_than(workspace2.terraform_version)
    assert not workspace2.is_terraform_version_older_than(workspace1.terraform_version)
    assert not workspace2.is_terraform_version_equal_to(workspace1.terraform_version)
    for workspace in [workspace1, workspace2, workspace3]:
        assert workspace4.is_terraform_version_newer_than(workspace.terraform_version)
        assert workspace.is_terraform_version_older_than(workspace4.terraform_version)
        assert not workspace.is_terraform_version_newer_than(workspace4.terraform_version)
        assert not workspace4.is_terraform_version_older_than(workspace.terraform_version)


def test_workspace_equality() -> None:
    workspace_id = ""
    workspace1 = Workspace(workspace_id, "", "0.12.28", False, False, "", "remote", True)
    workspace2 = Workspace(workspace_id, "", "0.13.1", False, False, "", "remote", True)
    workspace3 = Workspace(
        workspace_id + "something", "", "0.13.1", False, False, "", "remote", True
    )
    assert workspace1 == workspace2
    assert workspace1 != workspace3
    assert workspace1 != "not a workspace object"
