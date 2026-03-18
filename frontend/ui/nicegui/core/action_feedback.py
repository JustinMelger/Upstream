"""Shared user-facing feedback copy for common interactive actions."""

from __future__ import annotations


def _tracking_label(status: str) -> str:
    normalized = str(status or "").strip().lower()
    if normalized == "interested":
        return "Interested"
    if normalized == "in_progress":
        return "In Progress"
    if normalized == "completed":
        return "Completed"
    return "Not tracked"


def tracking_set_message(*, status: str) -> str:
    """Return standardized success text when tracking status is set."""
    return f"Tracking updated: {_tracking_label(status)}"


def tracking_cleared_message() -> str:
    """Return standardized success text when tracking status is cleared."""
    return "Tracking removed"


def path_selected_message() -> str:
    """Return standardized success text when a path is selected."""
    return "Path selected"


def path_unselected_message() -> str:
    """Return standardized success text when a path is unselected."""
    return "Path unselected"


def review_saved_message() -> str:
    """Return standardized success text when a review is saved."""
    return "Review saved"


def review_deleted_message() -> str:
    """Return standardized success text when a review is deleted."""
    return "Review deleted"
