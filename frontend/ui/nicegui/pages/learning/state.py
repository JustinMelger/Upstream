"""State model for the Learning page."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class LearningPageState:
    """Mutable page state for `/learning` UI rendering."""

    data: dict[str, Any] = field(default_factory=dict)
    loading: bool = False
    page_size: int = 12
    tracked_visible: int = 12
    selected_visible: int = 12
    dismissed_recommended_course_ids: set[int] = field(default_factory=set)
    dismissed_recommended_path_ids: set[int] = field(default_factory=set)
