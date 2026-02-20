"""State model for the AI Curator page."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AiCuratorPageState:
    """Mutable UI state for `/ai`."""

    draft_courses: list[dict[str, Any]] = field(default_factory=list)
    generating: bool = False
    applying: bool = False
