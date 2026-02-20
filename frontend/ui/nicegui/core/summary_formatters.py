"""Shared formatting helpers for rating/recommendation summary rows."""

from __future__ import annotations

from typing import Any, Literal


ReviewSummaryStyle = Literal["fraction", "star"]


def format_review_summary(row: dict[str, Any] | None, *, style: ReviewSummaryStyle = "fraction") -> str:
    """Format a review summary row into a compact badge label."""
    if not isinstance(row, dict):
        return ""
    try:
        count = int(row.get("review_count") or 0)
    except (TypeError, ValueError):
        count = 0
    if count <= 0:
        return ""
    try:
        avg = float(row.get("avg_rating") or 0.0)
    except (TypeError, ValueError):
        avg = 0.0
    if style == "star":
        return f"★ {avg:.1f} ({count})"
    return f"{avg:.1f}/5 ({count})"


def format_recommendation_summary(row: dict[str, Any] | None) -> str:
    """Format a recommendation summary row into a compact badge label."""
    if not isinstance(row, dict):
        return ""
    try:
        count = int(row.get("recommendation_count") or 0)
    except (TypeError, ValueError):
        count = 0
    if count <= 0:
        return ""
    return f"↗ {count} rec"
