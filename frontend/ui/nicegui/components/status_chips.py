"""Shared status label + chip-class helpers for NiceGUI pages.

This module exists to avoid cross-page imports between page modules.

The backend uses a small set of tracking/status values:
- `interested`
- `in_progress`
- `completed`

UI pages render these values as labels and colored "chips".
"""

from __future__ import annotations


TRACKING_STATUS_OPTIONS: list[tuple[str, str]] = [
    ("interested", "Interested"),
    ("in_progress", "In Progress"),
    ("completed", "Completed"),
]

# Paths "selected" statuses use the same domain vocabulary.
STATUS_OPTIONS: list[tuple[str, str]] = list(TRACKING_STATUS_OPTIONS)


def tracking_label(value: str | None) -> str:
    """Return a human-friendly label for a course tracking status.

    Args:
        value: Tracking status value.

    Returns:
        A stable label string (e.g. `"Interested"`), or `"Not tracked"` when
        the status is missing/unknown.
    """
    v = (value or "").strip()
    for key, label in TRACKING_STATUS_OPTIONS:
        if v == key:
            return label
    return "Not tracked"


def tracking_chip_class(value: str | None) -> str:
    """Return CSS classes for a tracking status chip."""
    v = (value or "").strip()
    if not v:
        return "lp-chip lp-chip--muted"
    if v == "interested":
        return "lp-chip lp-chip--sky"
    if v == "in_progress":
        return "lp-chip lp-chip--teal"
    if v == "completed":
        return "lp-chip lp-chip--lime"
    return "lp-chip"


def status_label(value: str | None) -> str:
    """Return a human-friendly label for a selected-path status.

    Args:
        value: Status value.

    Returns:
        A stable label string (e.g. `"Completed"`), or `"Not selected"` when
        the status is missing/unknown.
    """
    v = (value or "").strip()
    for key, label in STATUS_OPTIONS:
        if v == key:
            return label
    return "Not selected"


def status_chip_class(value: str | None) -> str:
    """Return CSS classes for a selected-path status chip."""
    # Same color mapping as tracking.
    return tracking_chip_class(value)
