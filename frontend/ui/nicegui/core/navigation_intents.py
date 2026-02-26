"""Ephemeral cross-page navigation intents for modal-opening flows."""

from __future__ import annotations

from typing import Any


_CATALOG_SHARE_STORAGE_KEY = "catalog_share_intent"


def set_catalog_share_storage_intent(*, storage_user: dict[str, Any], target: str) -> None:
    """Set one-shot catalog share intent in UI storage."""
    normalized = str(target or "").strip().lower()
    if normalized not in {"course", "path", "article"}:
        return
    storage_user[_CATALOG_SHARE_STORAGE_KEY] = normalized


def get_catalog_share_storage_intent(*, storage_user: dict[str, Any]) -> str | None:
    """Read catalog share intent from UI storage without consuming it."""
    value = storage_user.get(_CATALOG_SHARE_STORAGE_KEY)
    if not isinstance(value, str):
        return None
    normalized = str(value).strip().lower()
    return normalized if normalized in {"course", "path", "article"} else None


def pop_catalog_share_storage_intent(*, storage_user: dict[str, Any]) -> str | None:
    """Consume catalog share intent from UI storage."""
    value = storage_user.pop(_CATALOG_SHARE_STORAGE_KEY, None)
    if not isinstance(value, str):
        return None
    normalized = str(value).strip().lower()
    return normalized if normalized in {"course", "path", "article"} else None
