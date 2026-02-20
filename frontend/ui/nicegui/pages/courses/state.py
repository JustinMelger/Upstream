"""Typed state models for the Courses page."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class CoursesPageState:
    """Typed mutable state for the Courses page."""

    courses: list[dict[str, Any]] = field(default_factory=list)
    tracking_by_course_id: dict[int, dict[str, Any]] = field(default_factory=dict)
    review_summary_by_course_id: dict[int, dict[str, Any]] = field(default_factory=dict)
    recommendation_summary_by_course_id: dict[int, dict[str, Any]] = field(default_factory=dict)
