"""State model for the Teams page."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TeamsPageState:
    """Mutable UI state for `/teams`."""

    loading: bool = False
    teams: list[dict[str, Any]] = field(default_factory=list)
    selected_team_id: int | None = None
    selected_team: dict[str, Any] | None = None
    inbox_rows: list[dict[str, Any]] = field(default_factory=list)
    activity_rows: list[dict[str, Any]] = field(default_factory=list)
    error_message: str | None = None
