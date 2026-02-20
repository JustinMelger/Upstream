"""Ephemeral cross-page navigation intents for modal-opening flows."""

from __future__ import annotations

from typing import Any


_COURSE_INTENTS: dict[str, dict[str, Any]] = {}
_PATH_INTENTS: dict[str, dict[str, Any]] = {}
_COURSE_STORAGE_KEY = "courses_open_intent"
_PATH_STORAGE_KEY = "paths_open_intent"


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


def set_course_storage_intent(*, storage_user: dict[str, Any], course_id: int, view: str) -> None:
    """Set one-shot course dialog intent in UI storage."""
    storage_user[_COURSE_STORAGE_KEY] = {"course_id": int(course_id), "view": str(view or "full")}


def get_course_storage_intent(*, storage_user: dict[str, Any]) -> dict[str, Any] | None:
    """Read course dialog intent from UI storage without consuming it."""
    value = storage_user.get(_COURSE_STORAGE_KEY)
    return value if isinstance(value, dict) else None


def pop_course_storage_intent(*, storage_user: dict[str, Any]) -> dict[str, Any] | None:
    """Consume course dialog intent from UI storage."""
    value = storage_user.pop(_COURSE_STORAGE_KEY, None)
    return value if isinstance(value, dict) else None


def set_path_storage_intent(*, storage_user: dict[str, Any], path_id: int, view: str) -> None:
    """Set one-shot path dialog intent in UI storage."""
    storage_user[_PATH_STORAGE_KEY] = {"path_id": int(path_id), "view": str(view or "full")}


def get_path_storage_intent(*, storage_user: dict[str, Any]) -> dict[str, Any] | None:
    """Read path dialog intent from UI storage without consuming it."""
    value = storage_user.get(_PATH_STORAGE_KEY)
    return value if isinstance(value, dict) else None


def pop_path_storage_intent(*, storage_user: dict[str, Any]) -> dict[str, Any] | None:
    """Consume path dialog intent from UI storage."""
    value = storage_user.pop(_PATH_STORAGE_KEY, None)
    return value if isinstance(value, dict) else None
