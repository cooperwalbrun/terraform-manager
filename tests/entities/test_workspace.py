from terraform_manager.entities.workspace import Workspace


def test_version_comparisons() -> None:
    workspace1 = Workspace("", "", "0.12.28", False)
    workspace2 = Workspace("", "", "0.13.1", False)
    workspace3 = Workspace("", "", "0.13.1", False)
    assert workspace2.is_terraform_version_newer_than(str(workspace1.terraform_version))
    assert workspace1.is_terraform_version_older_than(str(workspace2.terraform_version))
    assert workspace2.is_terraform_version_equal_to(str(workspace3.terraform_version))
    assert not workspace1.is_terraform_version_newer_than(str(workspace2.terraform_version))
    assert not workspace2.is_terraform_version_older_than(str(workspace1.terraform_version))
    assert not workspace2.is_terraform_version_equal_to(str(workspace1.terraform_version))


def test_workspace_equality() -> None:
    workspace_id = ""
    workspace1 = Workspace(workspace_id, "", "0.12.28", False)
    workspace2 = Workspace(workspace_id, "", "0.13.1", False)
    workspace3 = Workspace(workspace_id + "something", "", "0.13.1", False)
    assert workspace1 == workspace2
    assert workspace1 != workspace3
    assert workspace1 != "not a workspace object"
