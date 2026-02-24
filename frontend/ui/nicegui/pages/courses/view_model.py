"""Presentation helpers (ViewModel) for the Courses page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.components.status_chips import tracking_chip_class, tracking_label
from frontend.ui.nicegui.core.datetime_utils import is_recent, parse_iso_datetime
from frontend.ui.nicegui.core.summary_formatters import format_recommendation_summary, format_review_summary


@dataclass(slots=True)
class CourseCardView:
    """Display fields for a single course card."""

    card_class_suffix: str
    is_new: bool
    is_updated: bool
    rating_badge: str
    recommendation_badge: str
    shared_by: str
    tracking_label_text: str
    tracking_chip_cls: str


def format_rating_badge(row: dict[str, Any] | None) -> str:
    """Format a compact rating badge for course cards (e.g., '★ 4.2 (12)')."""
    return format_review_summary(row, style="star")


def format_recommendation_badge(row: dict[str, Any] | None) -> str:
    """Format a compact recommendation badge for course cards."""
    return format_recommendation_summary(row)


def _status_for_card(tracked: dict[str, Any] | None) -> str:
    value = str((tracked or {}).get("status") or "").strip()
    if value in {"interested", "in_progress", "completed"}:
        return value
    return ""


def map_course_card_view(
    *,
    course_row: dict[str, Any],
    tracked_row: dict[str, Any] | None,
    review_summary_row: dict[str, Any] | None,
    recommendation_summary_row: dict[str, Any] | None,
) -> CourseCardView:
    """Map course + state payloads to card display values."""
    status = _status_for_card(tracked_row)
    created_at = parse_iso_datetime(course_row.get("created_at"))
    updated_at = parse_iso_datetime(course_row.get("updated_at"))
    is_updated = is_recent(updated_at) and created_at is not None and updated_at is not None and updated_at > created_at
    is_new = (not is_updated) and is_recent(created_at)
    return CourseCardView(
        card_class_suffix=f" lp-course-card--{status}" if status else "",
        is_new=is_new,
        is_updated=is_updated,
        rating_badge=format_rating_badge(review_summary_row),
        recommendation_badge=format_recommendation_badge(recommendation_summary_row),
        shared_by=str(course_row.get("created_by") or "").strip(),
        tracking_label_text=tracking_label((tracked_row or {}).get("status")),
        tracking_chip_cls=tracking_chip_class((tracked_row or {}).get("status")),
    )
