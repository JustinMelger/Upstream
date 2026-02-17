"""Ephemeral cross-page navigation intents for modal-opening flows."""

from __future__ import annotations

from typing import Any


_COURSE_INTENTS: dict[str, dict[str, Any]] = {}
_PATH_INTENTS: dict[str, dict[str, Any]] = {}


def set_course_intent(*, username: str, course_id: int, view: str) -> None:
    """Set one-shot course dialog intent for a user."""
    _COURSE_INTENTS[str(username)] = {"course_id": int(course_id), "view": str(view or "full")}


def get_course_intent(*, username: str) -> dict[str, Any] | None:
    """Read course dialog intent without consuming it."""
    return _COURSE_INTENTS.get(str(username))


def pop_course_intent(*, username: str) -> dict[str, Any] | None:
    """Consume course dialog intent for a user."""
    return _COURSE_INTENTS.pop(str(username), None)


def set_path_intent(*, username: str, path_id: int, view: str) -> None:
    """Set one-shot path dialog intent for a user."""
    _PATH_INTENTS[str(username)] = {"path_id": int(path_id), "view": str(view or "full")}


def get_path_intent(*, username: str) -> dict[str, Any] | None:
    """Read path dialog intent without consuming it."""
    return _PATH_INTENTS.get(str(username))


def pop_path_intent(*, username: str) -> dict[str, Any] | None:
    """Consume path dialog intent for a user."""
    return _PATH_INTENTS.pop(str(username), None)
