import time
from datetime import datetime
from typing import Dict, List

from terraform_manager.entities.workspace import Workspace

_dead_statuses: List[str] = [
    "planned_and_finished", "applied", "discarded", "errored", "canceled", "force_canceled"
]


class Run:
    def __init__(self, *, workspace: Workspace, status: str, all_status_timestamps: Dict[str, str]):
        self.workspace = workspace
        self.status = status
        self.all_status_timestamps = all_status_timestamps

        current_timestamp = all_status_timestamps.get(status + "-at")
        if current_timestamp is not None:
            try:
                if "+" in current_timestamp:
                    # We need to transform the +HH:MM format that HashiCorp returns into +HHMM in
                    # order for the string to work with the %z flag used with datetime.strptime()
                    # Python 3 reference for the possible flags for datetime.strptime():
                    # https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes
                    parts = current_timestamp.split("+")
                    reformatted_zone = parts[1].replace(":", "")
                    fixed_form = f"{parts[0]}+{reformatted_zone}"
                else:
                    fixed_form = current_timestamp
                self.status_unix_time: int = round(
                    time.mktime(datetime.strptime(fixed_form, "%Y-%m-%dT%H:%M:%S%z").timetuple())
                )
            except:
                self.status_unix_time: int = 0
        else:
            self.status_unix_time: int = 0

        self.is_active: bool = status not in _dead_statuses

    def __repr__(self) -> str:
        return (
            f"Run(workspace={self.workspace.name}, status={self.status}, "
            f"status_unix_time={self.status_unix_time}, is_active={self.is_active})"
        )

    def __str__(self) -> str:
        return repr(self)
