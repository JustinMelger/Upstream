"""UI sections for the Activity page."""

from __future__ import annotations

from collections.abc import Callable
import logging
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.feedback import render_empty_block, render_error_block
from frontend.ui.nicegui.pages.activity.ui_glue import coerce_target_id, format_when


logger = logging.getLogger(__name__)


def render_empty_activity(*, current_tab: str, on_primary: Callable[[], None]) -> None:
    """Render empty-state card for activity list."""
    if str(current_tab or "inbox") == "team":
        render_empty_block(
            title="No activity yet.",
            description="When teammates share, recommend, or rate content, updates will appear here.",
            primary_label="Explore",
            on_primary=on_primary,
        )
        return
    render_empty_block(
        title="No activity yet.",
        description="When teammates review or recommend your shared content, updates will appear here.",
        primary_label="Explore",
        on_primary=on_primary,
    )


def render_activity_error(*, message: str, on_retry: Callable[[], Any]) -> None:
    """Render load-error state card for activity list."""
    render_error_block(
        title="Could not load activity.",
        message=str(message or "Unexpected error"),
        retry_label="Retry",
        on_retry=on_retry,
    )


def render_activity_items(*, events: list[dict[str, Any]], on_open: Callable[[str, int], Any]) -> None:
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
