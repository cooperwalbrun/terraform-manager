from asciimatics.exceptions import StopApplication
from asciimatics.screen import Screen
from asciimatics.widgets import Frame, Widget, Layout, MultiColumnListBox, Label, Divider
from terraform_manager.interface.run_watcher.active_runs_view_shared_state import \
    ActiveRunsViewSharedState
from terraform_manager.terraform import TARGETING_SPECIFIC_WORKSPACES_TEXT

_minimum_seconds_between_fetches: float = 12.0


class ActiveRunsView(Frame):
    def __init__(
        self,
        shared_state: ActiveRunsViewSharedState,
        screen: Screen,
        *,
        minimum_seconds_between_fetches: float
    ):
        super(ActiveRunsView, self).__init__(
            screen,
            screen.height,
            screen.width,
            on_load=self._rerender,
            has_border=False,
            can_scroll=True,
            title="Current Active Runs"
        )

        # See: https://asciimatics.readthedocs.io/en/stable/widgets.html#colour-schemes
        self.set_theme("monochrome")

        self._shared_state = shared_state
        self._minimum_seconds_between_fetches = minimum_seconds_between_fetches

        # Below are the widths (as percentages) of the columns of the data table - these should
        # total 100% for proper display behavior
        workspace_header_width = 37
        created_header_width = 23
        status_header_width = 17
        timestamp_header_width = 23

        # Set up the headers widgets
        # divider = VerticalDivider()
        headers = [
            Label(text, height=1, align="^")
            for text in ["Workspace", "Created", "Status", "Status As Of"]
        ]
        headers_widths = [
            workspace_header_width,
            created_header_width,
            status_header_width,
            timestamp_header_width
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
                f"^{created_header_width}%",
                f"^{status_header_width}%",
                f">{timestamp_header_width}%"
            ],
            add_scroll_bar=False,
            options=self._shared_state.get_empty_state_data(),
            name="active_runs"
        )

        # Set up the parent layout of the data table widget
        table_layout = Layout([100], fill_frame=True)
        self.add_layout(table_layout)
        table_layout.add_widget(self._table_list_box, column=0)

        if self._shared_state.targeting_specific_workspaces:
            divider = Divider(draw_line=True)
            partial_target_warning = Label(TARGETING_SPECIFIC_WORKSPACES_TEXT)
            partial_target_layout = Layout([100])
            self.add_layout(partial_target_layout)
            partial_target_layout.add_widget(divider)
            partial_target_layout.add_widget(partial_target_warning)

        # Finally, we are done creating the interface - the last thing we must do is call self.fix()
        self.fix()

    def _rerender(self) -> None:
        # This method is the core driver of this view - it is called on every re-render triggered by
        # asciimatics (which is based on the frame rate and the length of the "scene" which contains
        # this view - see terraform/runs.py for more information
        self._shared_state.fetch_current_runs_if_needed(self._minimum_seconds_between_fetches)
        self._table_list_box.options = self._shared_state.get_table_data()

    @staticmethod
    def _quit() -> None:  # pragma: no cover
        raise StopApplication("User exited the program")
