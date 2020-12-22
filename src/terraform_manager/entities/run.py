from typing import Dict, Optional, List

from terraform_manager.entities.workspace import Workspace

_dead_statuses: List[str] = [
    "planned_and_finished", "applied", "discarded", "errored", "canceled", "force_canceled"
]


class Run:
    def __init__(
        self,
        *,
        workspace: Workspace,
        status: str,
        all_status_timestamps: Dict[str, str],
        created_by: str
    ):
        self.workspace = workspace
        self.status = status
        self.all_status_timestamps = all_status_timestamps
        self.created_by = created_by

        self.status_timestamp: Optional[str] = all_status_timestamps.get(status + "-at")
        self.is_active: bool = status not in _dead_statuses

    def __repr__(self) -> str:
        return (
            f"Run(workspace={self.workspace.name}, status={self.status}, "
            f"status_timestamp={self.status_timestamp}, created_by={self.created_by}, "
            f"is_active={self.is_active})"
        )

    def __str__(self) -> str:
        return repr(self)
