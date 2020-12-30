import random
import string
from typing import Optional, Dict
from unittest.mock import MagicMock

from pytest_mock import MockerFixture
from terraform_manager.entities.run import Run
from terraform_manager.entities.workspace import Workspace
from terraform_manager.terraform import CLOUD_DOMAIN

TEST_ORGANIZATION: str = "test"
TEST_TERRAFORM_DOMAIN: str = CLOUD_DOMAIN
TEST_API_URL: str = f"https://{TEST_TERRAFORM_DOMAIN}/api/v2"


def test_workspace(
    *,
    version: str = "0.13.1",
    locked: bool = False,
    working_directory: str = "",
    agent_pool_id: str = "",
    execution_mode: str = "remote",
    speculative: bool = True
) -> Workspace:
    letters = string.ascii_lowercase
    return Workspace(
        workspace_id="".join([random.choice(letters) for _ in range(5)]),
        name="".join([random.choice(letters) for _ in range(5)]),
        terraform_version=version,
        auto_apply=False,
        is_locked=locked,
        working_directory=working_directory,
        agent_pool_id=agent_pool_id,
        execution_mode=execution_mode,
        speculative=speculative
    )


def test_run(
    *,
    status: str = "planned",
    all_status_timestamps: Optional[Dict[str, str]] = None,
    created_at: str = "2020-11-05T04:29:38.792Z",
    has_changes: bool = True
) -> Run:
    letters = string.ascii_lowercase
    times = {"planned-at": "2020-11-05T04:30:09+00:00"}
    return Run(
        run_id="".join([random.choice(letters) for _ in range(5)]),
        workspace=test_workspace(),
        created_at=created_at,
        status=status,
        all_status_timestamps=times if all_status_timestamps is None else all_status_timestamps,
        has_changes=has_changes
    )


def establish_asciimatics_widget_mocks(mocker: MockerFixture) -> Dict[str, MagicMock]:
    frame_mocks = {
        f"Frame.{method}": mocker.patch(f"asciimatics.widgets.Frame.{method}", return_value=None)
        for method in ["__init__", "set_theme", "add_layout", "fix"]
    }
    layout_mocks = {
        f"Layout.{method}": mocker.patch(f"asciimatics.widgets.Layout.{method}", return_value=None)
        for method in ["add_widget"]
    }
    return {**frame_mocks, **layout_mocks}
