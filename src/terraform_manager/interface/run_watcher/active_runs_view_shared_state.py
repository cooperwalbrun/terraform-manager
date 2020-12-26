import time
from datetime import datetime
from threading import Lock
from typing import List, Callable

import timeago
from terraform_manager.entities.run import Run
from terraform_manager.interface.run_watcher import MultiColumnListViewOption


def _beautify(table_row: List[str]) -> List[str]:
    now = datetime.utcnow()
    created_time_ago = timeago.format(datetime.utcfromtimestamp(float(table_row[1])), now)
    status_time_ago = timeago.format(datetime.utcfromtimestamp(float(table_row[3])), now)
    return [table_row[0], created_time_ago, table_row[2], status_time_ago]


class ActiveRunsViewSharedState:
    """
    It is very important for this state entity to live outside of the ActiveRunsView class; when the
    window is being resized, it will force very rapid re-instantiations of the ActiveRunsView class,
    which in turn would trigger very rapid re-fetches from the Terraform API or rapid updates to
    time-sensitive state. This class exists specifically for maintaining state beyond the lifecycle
    of the ActiveRunsView class, and an instance of this class should be shared across all
    ActiveRunsView class instances.
    """
    def __init__(
        self, *, run_generator: Callable[[], List[Run]], targeting_specific_workspaces: bool
    ):
        self._run_lock: Lock = Lock()
        self.runs: List[Run] = []
        self.run_generator = run_generator
        self.last_api_call: float = 0.0

        self._clock_check_lock: Lock = Lock()
        self.last_clock_check: float = 0.0
        self.clock_check_counter: int = -1

        self.targeting_specific_workspaces = targeting_specific_workspaces

    def fetch_current_runs_if_needed(self, minimum_seconds_between_fetches: float) -> None:
        with self._run_lock:
            if time.time() - self.last_api_call >= minimum_seconds_between_fetches:
                # This is an expensive operation because self.run_generator() is expected to call
                # the Terraform API
                self.last_api_call = time.time()
                self.runs = self.run_generator()

    def _get_periods(self) -> str:
        with self._clock_check_lock:
            if time.time() - self.last_clock_check >= 1.0:
                self.last_clock_check = time.time()
                self.clock_check_counter = (self.clock_check_counter + 1) % 4
            return self.clock_check_counter * "."

    def get_empty_state_data(self) -> List[MultiColumnListViewOption]:
        time_ago = timeago.format(datetime.utcfromtimestamp(self.last_api_call), datetime.utcnow())
        row = [f"none currently", "n/a", "waiting" + self._get_periods(), time_ago]
        return [(row, 0)]

    def get_table_data(self) -> List[MultiColumnListViewOption]:
        with self._run_lock:
            options = []
            for index, run in enumerate(self.runs):
                row = [
                    run.workspace.name,
                    str(run.created_at_unix_time),
                    run.status,
                    str(run.status_unix_time)
                ]
                options.append((row, index))
            if len(options) == 0:
                return self.get_empty_state_data()
            else:
                # The sort operations below require the sorted() function to use a stable sorting
                # algorithm internally (otherwise the end result would not be ordered as desired)
                sorted_options = sorted(options, key=lambda x: (x[0][0], x[0][2]))
                sorted_options = sorted(
                    sorted_options, key=lambda x: (x[0][3], x[0][1]), reverse=True
                )
                return [(_beautify(row), index) for row, index in sorted_options]

    def __repr__(self) -> str:
        return (
            f"ActiveRunsViewSharedState(runs=List[{len(self.runs)}]), "
            f"last_api_call={self.last_api_call}, last_clock_check={self.last_clock_check}, "
            f"clock_check_counter={self.clock_check_counter})"
        )

    def __str__(self) -> str:
        return repr(self)
