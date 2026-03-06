"""Reusable card action controls."""

from __future__ import annotations

from typing import Any, Callable

from nicegui import ui

from frontend.ui.nicegui.core.a11y import apply_icon_button_a11y


def render_view_review_actions(
    *,
    on_view: Callable[..., Any],
    on_review: Callable[..., Any],
    review_tooltip: str = "Review",
    on_copy: Callable[..., Any] | None = None,
) -> None:
    """Render shared icon actions used on content cards."""
    apply_icon_button_a11y(
        ui.button("", icon="visibility", on_click=on_view).props("outline dense"),
        label="View details",
        tooltip="View",
    )
    apply_icon_button_a11y(
        ui.button("", icon="rate_review", on_click=on_review).props("outline dense"),
        label="Review item",
        tooltip=review_tooltip,
    )
    if on_copy is not None:
        apply_icon_button_a11y(
            ui.button("", icon="content_copy", on_click=on_copy).props("outline dense"),
            label="Copy link",
            tooltip="Copy link",
        )
