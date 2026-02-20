"""State model for the Activity page."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ActivityPageState:
    """Mutable UI state for `/activity`."""

    events: list[dict[str, Any]] = field(default_factory=list)
    loading: bool = False
    pending_reload: bool = False
    error_message: str | None = None
