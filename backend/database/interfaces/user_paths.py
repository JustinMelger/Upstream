from __future__ import annotations

from typing import Protocol

from backend.database.models import SelectedPathRecord


class UserPathsRepository(Protocol):
    def add_user_path(self, colleague_id: str, path_id: int, now: str) -> int:
        """Insert a user_path selection if missing."""

    def list_user_paths(self, colleague_id: str) -> list[SelectedPathRecord]:
        """List selected paths for a user."""

    def remove_user_path(self, colleague_id: str, path_id: int) -> int:
        """Remove a selected path."""

    def update_user_path_status(self, colleague_id: str, path_id: int, status: str, now: str) -> int:
        """Update status for a selected path."""
