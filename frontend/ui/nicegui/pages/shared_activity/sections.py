"""Shared UI sections for activity-style feed rendering."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.feedback import render_empty_block, render_error_block
from frontend.ui.nicegui.core.feed_copy import activity_empty_description
from frontend.ui.nicegui.pages.shared_activity.ui_glue import format_when


def render_empty_activity(*, current_tab: str, on_primary: Callable[[], None]) -> None:
    """Render empty-state card for a shared activity feed."""
    render_empty_block(
        title="No activity yet.",
        description=activity_empty_description(current_tab=str(current_tab or "inbox")),
        primary_label="Explore",
        on_primary=on_primary,
    )


def render_activity_error(*, message: str, on_retry: Callable[[], Any]) -> None:
    """Render load-error state card for a shared activity feed."""
    render_error_block(
        title="Could not load activity.",
        message=str(message or "Unexpected error"),
        retry_label="Retry",
        on_retry=on_retry,
    )


def render_activity_items(*, events: list[Any], on_open: Callable[[Any], Any]) -> None:
    """Render compact shared activity feed rows."""
    with ui.column().classes("w-full gap-0 lp-teams-feed"):
        for event in list(events or []):
            with ui.element("div").classes("w-full lp-teams-feed-row"):
                with ui.row().classes("items-center gap-4 w-full no-wrap"):
                    ui.icon("auto_stories").classes("text-[18px]").style("color: var(--lp-primary-strong)")
                    with ui.column().classes("gap-1 min-w-0 flex-1"):
                        ui.label(str(event.message or "Activity update")).classes("text-sm lp-teams-feed-row-title")
                    meta_parts = [
                        str(event.actor or "").strip(),
                        str(event.target.target_type_label or "").strip(),
                        str(event.target.interaction_label or "").strip(),
                    ]
                    if str(event.target.target_label or "").strip():
                        meta_parts.append(str(event.target.target_label or "").strip())
                    meta = " · ".join(part for part in meta_parts if part)
                    ui.label(meta).classes("text-xs lp-teams-feed-row-meta").style("color: var(--lp-muted)")
                    ui.label(format_when(event.created_at)).classes("text-xs lp-teams-item-time").style(
                        "color: var(--lp-muted)"
                    )
                    ui.button("Open", on_click=lambda target=event.target: on_open(target)).props(
                        "dense flat color=primary"
                    ).classes("lp-teams-open-btn")


def render_activity_feed(
    *,
    events: list[Any],
    on_open: Callable[[Any], Any],
    empty_title: str,
    empty_description: str,
    compact: bool = True,
) -> None:
    """Render a shared activity feed with a caller-provided empty state."""
    if not events:
        render_empty_block(
            title=str(empty_title or "No activity yet."),
            description=str(empty_description or ""),
            compact=compact,
        )
        return
    render_activity_items(events=events, on_open=on_open)
