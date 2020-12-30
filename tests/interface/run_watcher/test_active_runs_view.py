from typing import List, Optional
from unittest.mock import MagicMock

from pytest_mock import MockerFixture
from terraform_manager.entities.run import Run
from terraform_manager.interface.run_watcher import MultiColumnListViewOption
from terraform_manager.interface.run_watcher.active_runs_view import ActiveRunsView
from terraform_manager.interface.run_watcher.active_runs_view_shared_state import \
    ActiveRunsViewSharedState

from tests.utilities.tooling import test_run, establish_asciimatics_widget_mocks

_test_run: Run = test_run()
_shared_state_class: str = (
    "terraform_manager.interface.run_watcher.active_runs_view_shared_state"
    ".ActiveRunsViewSharedState"
)


def _run_generator_mock(runs: Optional[List[Run]] = None) -> MagicMock:
    run_generator_mock: MagicMock = MagicMock()
    run_generator_mock.return_value = [_test_run] if runs is None else runs
    return run_generator_mock


def test_rerender(mocker: MockerFixture) -> None:
    for targeting_specific_workspaces in [True, False]:
        establish_asciimatics_widget_mocks(mocker)
        screen_mock: MagicMock = MagicMock()
        run_generator_mock: MagicMock = _run_generator_mock()
        table_data: List[MultiColumnListViewOption] = [(["test", "test", "test", "test"], 0)]
        mocker.patch(f"{_shared_state_class}.get_table_data", return_value=table_data)

        state = ActiveRunsViewSharedState(
            run_generator=run_generator_mock,
            targeting_specific_workspaces=targeting_specific_workspaces
        )
        view = ActiveRunsView(state, screen_mock, minimum_seconds_between_fetches=10.0)

        view._rerender()
        assert view._table_list_box.options == table_data
