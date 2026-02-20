"""UI sections for the Activity page."""

from __future__ import annotations

import logging
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.pages.activity.ui_glue import coerce_target_id, format_when

logger = logging.getLogger(__name__)


def render_empty_activity(*, current_tab: str) -> None:
    """Render empty-state card for activity list."""
    with ui.card().classes("lp-card w-full"):
        ui.label("No activity yet.").classes("text-base")
        if str(current_tab or "inbox") == "team":
            ui.label("When teammates share, recommend, or rate content, updates will appear here.").classes("text-sm").style(
                "color: var(--lp-muted)"
            )
        else:
            ui.label("When teammates review or recommend your shared content, updates will appear here.").classes("text-sm").style(
                "color: var(--lp-muted)"
            )


def render_activity_error(*, message: str) -> None:
    """Render load-error state card for activity list."""
    with ui.card().classes("lp-card w-full"):
        ui.label("Could not load activity.").classes("text-base")
        ui.label(str(message or "Unexpected error")).classes("text-sm").style("color: var(--lp-muted)")


def render_activity_items(*, events: list[dict[str, Any]], on_open: Any) -> None:
    """Render activity cards."""
    with ui.column().classes("w-full gap-3"):
        for row in list(events or []):
            message = str(row.get("message") or "").strip()
            actor = str(row.get("actor") or "").strip()
            created_at = str(row.get("created_at") or "").strip()
            target_type = str(row.get("target_type") or "").strip()
            target_label = str(row.get("target_label") or "").strip()
            target_id = coerce_target_id(row.get("target_id"))
            if target_id is None:
                logger.warning("Skipping activity row with invalid target_id", extra={"activity_row": row})
                continue
            with ui.card().classes("lp-card w-full"):
                with ui.row().classes("items-center justify-between w-full"):
                    ui.label(message or "Activity update").classes("text-sm")
                    ui.label(format_when(created_at)).classes("text-xs").style("color: var(--lp-muted)")
                with ui.row().classes("items-center justify-between w-full mt-2"):
                    meta = actor
                    if target_label:
                        meta = f"{meta} · {target_label}" if meta else target_label
                    ui.label(meta).classes("text-xs").style("color: var(--lp-muted)")
                    ui.button("Open", on_click=lambda t=target_type, tid=target_id: on_open(t, tid)).props("dense outline")
