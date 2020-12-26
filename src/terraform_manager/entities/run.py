from typing import Dict, List

from terraform_manager.entities.workspace import Workspace
from terraform_manager.utilities.utilities import convert_hashicorp_timestamp_to_unix_time, \
    convert_timestamp_to_unix_time

_dead_statuses: List[str] = [
    "planned_and_finished", "applied", "discarded", "errored", "canceled", "force_canceled"
]


class Run:
    def __init__(
        self,
        *,
        workspace: Workspace,
        created_at: str,
        status: str,
        all_status_timestamps: Dict[str, str],
        has_changes: bool
    ):
        self.workspace = workspace
        self.created_at = created_at
        self.status = status
        self.all_status_timestamps = all_status_timestamps
        self.has_changes = has_changes

        created_at_unix_time = convert_timestamp_to_unix_time(
            # The created_at timestamp is in the format "2017-11-28T22:52:46.711Z", and Z indicates
            # that it is already a UTC time, so we tell the conversion function this explicitly
            created_at.split(".")[0] + "UTC",
            "%Y-%m-%dT%H:%M:%S%Z"  # Note the %Z (which will capture the "UTC" we appended above)
        )
        if created_at_unix_time is None:
            self.created_at_unix_time: int = 0
        else:
            self.created_at_unix_time: int = created_at_unix_time

        current_timestamp = all_status_timestamps.get(status + "-at")
        if current_timestamp is None:
            self.status_unix_time: int = 0
        else:
            status_unix_time = convert_hashicorp_timestamp_to_unix_time(current_timestamp)
            self.status_unix_time: int = 0 if status_unix_time is None else status_unix_time

        self.is_active: bool = status not in _dead_statuses

    def __repr__(self) -> str:
        return (
            f"Run(workspace={self.workspace.name}, "
            f"created_at_unix_time={self.created_at_unix_time}, status={self.status}, "
            f"status_unix_time={self.status_unix_time}, is_active={self.is_active}, "
            f"has_changes={self.has_changes})"
        )

    def __str__(self) -> str:
        return repr(self)
