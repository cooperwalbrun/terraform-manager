import time
from datetime import datetime
from typing import Callable, List, Tuple

import timeago
from asciimatics.exceptions import StopApplication
from asciimatics.screen import Screen
from asciimatics.widgets import Frame, Widget, Layout, MultiColumnListBox, Label, VerticalDivider
from terraform_manager.entities.run import Run

MultiColumnListViewOption = Tuple[List[str], int]

_headers: List[str] = ["Workspace", "Run Status", "Status Since"]
_minimum_seconds_between_fetches: float = 15.0

# It is very important for the following variables to live outside of the class below; when the
# window is being resized, it will force very rapid re-instantiations of the ActiveRunsView class,
# which in turn will trigger very rapid re-fetches from the Terraform API. The throttling that is in
# place elsewhere in this program would guard against this, but it is better to be explicit here and
# keep the API call variable separate from the class's lifecycle.
_runs: List[Run] = []
_last_api_call: float = 0.0


def _get_empty_state_data() -> List[MultiColumnListViewOption]:
    time_ago = timeago.format(
        datetime.utcfromtimestamp(_last_api_call), datetime.utcfromtimestamp(time.time())
    )
    return [([f"None as of {time_ago}", "", "", ""], 0)]


def _get_table_data() -> List[MultiColumnListViewOption]:
    options = []
    for index, run in enumerate(_runs):
        row = [run.workspace.name, run.status, run.status_timestamp, run.created_by]
        options.append((row, index))
    return _get_empty_state_data() if len(options) == 0 else options


class ActiveRunsView(Frame):
    def __init__(
        self,
        screen: Screen,
        organization: str,
        *,
        run_generator: Callable[[], List[Run]],
        targeting_specific_workspaces: bool
    ):
        super(ActiveRunsView, self).__init__(
            screen,
            screen.height,
            screen.width,
            on_load=self._refresh,
            has_border=True,
            can_scroll=True,
            title="Current Active Runs"
        )

        # See: https://asciimatics.readthedocs.io/en/stable/widgets.html#colour-schemes
        self.set_theme("monochrome")

        self._organization = organization
        self._run_generator = run_generator
        self._targeting_specific_workspaces = targeting_specific_workspaces

        # Below are the widths (as percentages) of the columns of the data table
        workspace_header_width = 45
        status_header_width = 15
        timestamp_header_width = 20
        created_by_width = 20

        # Set up the headers widgets
        # divider = VerticalDivider()
        headers = [
            Label(text, height=1, align="^")
            for text in ["Workspace", "Status", "Timestamp", "Created By"]
        ]
        headers_widths = [
            workspace_header_width, status_header_width, timestamp_header_width, created_by_width
        ]

        # Set up the parent layout of the headers widgets
        headers_layout = Layout(headers_widths, fill_frame=False)
        self.add_layout(headers_layout)
        for index, header in enumerate(headers):
            headers_layout.add_widget(header, column=index)

        # Set up the data table widget and its parent layout
        self._table_list_box: MultiColumnListBox = MultiColumnListBox(
            Widget.FILL_FRAME,
            columns=[
                f"<{workspace_header_width}%",
                f"^{status_header_width}%",
                f">{timestamp_header_width}%",
                f"<{created_by_width}%"
            ],
            options=_get_empty_state_data(),
            name="active_runs"
        )

        # Set up the parent layout of the data table widget
        table_layout = Layout([100], fill_frame=True)
        self.add_layout(table_layout)
        table_layout.add_widget(self._table_list_box, column=0)

        # Finally, we are done creating the interface - the last thing we must do is call self.fix()
        self.fix()

    def _fetch_current_runs(self) -> None:
        global _runs, _last_api_call
        if round(time.time() - _last_api_call) >= _minimum_seconds_between_fetches:
            # This is an expensive operation because self.run_generator() is expected to call the
            # Terraform API
            _runs = self._run_generator()
            _last_api_call = time.time()

    def _refresh(self) -> None:
        self._fetch_current_runs()
        self._table_list_box.options = _get_table_data()

    @staticmethod
    def _quit() -> None:
        raise StopApplication("User exited the program")
