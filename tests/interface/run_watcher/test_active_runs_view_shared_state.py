import time
from datetime import datetime
from typing import List
from unittest.mock import MagicMock

from terraform_manager.entities.run import Run
from terraform_manager.interface.run_watcher.active_runs_view_shared_state import \
    ActiveRunsViewSharedState

from tests.utilities.tooling import test_run


def _run_generator_mock(runs: List[Run]) -> MagicMock:
    run_generator_mock: MagicMock = MagicMock()
    run_generator_mock.return_value = runs
    return run_generator_mock


def test_get_periods() -> None:
    state = ActiveRunsViewSharedState(run_generator=lambda: [], targeting_specific_workspaces=False)
    assert state._get_periods() == ""
    time.sleep(1.0)
    assert state._get_periods() == "."
    time.sleep(1.0)
    assert state._get_periods() == ".."
    time.sleep(1.0)
    assert state._get_periods() == "..."
    time.sleep(1.0)
    assert state._get_periods() == ""


def test_fetch_current_runs_if_needed() -> None:
    run = test_run()
    run_generator_mock: MagicMock = _run_generator_mock([run])
    state = ActiveRunsViewSharedState(
        run_generator=run_generator_mock, targeting_specific_workspaces=False
    )

    state.fetch_current_runs_if_needed(1.0)
    state.fetch_current_runs_if_needed(1.0)
    assert state.runs == [run]
    run_generator_mock.assert_called_once()


def test_get_empty_state_data() -> None:
    state = ActiveRunsViewSharedState(run_generator=lambda: [], targeting_specific_workspaces=False)
    state.last_api_call = time.time()
    row = [f"none currently", "n/a", "waiting", "just now"]
    assert state.get_empty_state_data() == [(row, 0)]
    assert state.get_table_data() == [(row, 0)]


def test_get_table_data() -> None:
    now = datetime.utcnow()
    run = test_run(
        status="planned",
        created_at=now.strftime("%Y-%m-%dT%H:%M:%S") + ".000Z",
        all_status_timestamps={"planned-at": now.strftime("%Y-%m-%dT%H:%M:%S") + "+00:00"}
    )
    state = ActiveRunsViewSharedState(run_generator=lambda: [], targeting_specific_workspaces=False)
    state.runs = [run]
    row = [run.workspace.name, "just now", run.status, "just now"]
    assert state.get_table_data() == [(row, 0)]
