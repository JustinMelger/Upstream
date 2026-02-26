"""Helpers for suggestion-origin UI indicators."""

from __future__ import annotations


def suggestion_badge_text(*, current_value: str, suggested_value: str) -> str:
    """Return label text for a field with suggested content state."""
    current = str(current_value or "").strip()
    suggested = str(suggested_value or "").strip()
    if not suggested:
        return ""
    if current == suggested:
        return "Suggested"
    return "Edited from suggestion"
