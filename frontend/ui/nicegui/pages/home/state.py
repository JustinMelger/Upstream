"""State model for the Insights page."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class HomePageState:
    """Mutable UI state for `/insights`."""

    snapshot_stats: dict[str, int] = field(default_factory=dict)
    team_stats_by_user: list[dict[str, Any]] = field(default_factory=list)
    loading: bool = False
    pending_reload: bool = False
