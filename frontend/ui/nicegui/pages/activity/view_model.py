"""Typed view-model helpers for activity-like feeds."""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any

from frontend.ui.nicegui.core.learning_items import learning_item_capabilities, learning_item_type_label
from frontend.ui.nicegui.core.navigation import build_activity_target_link
from frontend.ui.nicegui.pages.activity.ui_glue import coerce_target_id


logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ActivityTargetView:
    """Normalized activity target metadata for UI renderers."""

    target_type: str
    target_id: int
    target_label: str
    target_family: str
    open_url: str

    @property
    def target_type_label(self) -> str:
        """Return a user-facing type label."""
        if self.target_family == "learning_item":
            return learning_item_type_label(self.target_type)
        if self.target_type == "path":
            return "Path"
        return "Item"

    @property
    def interaction_label(self) -> str:
        """Return the current interaction model for the target."""
        if self.target_family == "learning_item":
            capabilities = learning_item_capabilities(self.target_type)
            if capabilities.supports_tracking:
                return "tracking + reviews"
            if capabilities.supports_reviews:
                return "reviews"
            return "details only"
        if self.target_type == "path":
            return "path progress"
        return "details"


@dataclass(slots=True)
class ActivityEventView:
    """Typed projection for one activity feed row."""

    message: str
    actor: str
    created_at: str
    target: ActivityTargetView


def _normalize_target_type(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"course", "article", "video", "path"}:
        return normalized
    return "unknown"


def build_activity_target_view(*, target_type: Any, target_id: Any, target_label: Any) -> ActivityTargetView | None:
    """Normalize one activity target payload."""
    normalized_type = _normalize_target_type(target_type)
    normalized_id = coerce_target_id(target_id)
    if normalized_id is None:
        return None
    target_family = "learning_item" if normalized_type in {"course", "article", "video"} else normalized_type
    return ActivityTargetView(
        target_type=normalized_type,
        target_id=normalized_id,
        target_label=str(target_label or "").strip(),
        target_family=target_family,
        open_url=build_activity_target_link(target_type=normalized_type, target_id=normalized_id),
    )


def build_activity_event_views(*, events: list[dict[str, Any]]) -> list[ActivityEventView]:
    """Build typed activity feed rows and skip invalid targets."""
    out: list[ActivityEventView] = []
    for row in list(events or []):
        target = build_activity_target_view(
            target_type=row.get("target_type"),
            target_id=row.get("target_id"),
            target_label=row.get("target_label"),
        )
        if target is None:
            logger.warning("Skipping activity row with invalid target_id", extra={"activity_row": row})
            continue
        out.append(
            ActivityEventView(
                message=str(row.get("message") or "").strip(),
                actor=str(row.get("actor") or "").strip(),
                created_at=str(row.get("created_at") or "").strip(),
                target=target,
            )
        )
    return out
