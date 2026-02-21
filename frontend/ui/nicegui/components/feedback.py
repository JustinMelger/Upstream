"""Reusable empty/error feedback blocks for page sections."""

from __future__ import annotations

from typing import Any

from nicegui import ui


def render_empty_block(
    *,
    title: str,
    description: str | None = None,
    primary_label: str | None = None,
    on_primary: Any | None = None,
    secondary_label: str | None = None,
    on_secondary: Any | None = None,
) -> None:
    """Render a consistent empty-state block with optional CTA actions."""
    with ui.card().classes("lp-card w-full"):
        ui.label(str(title or "")).classes("text-sm")
        if str(description or "").strip():
            ui.label(str(description or "")).classes("text-sm").style("color: var(--lp-muted)")
        if primary_label or secondary_label:
            with ui.row().classes("items-center gap-2 mt-2"):
                if primary_label and on_primary is not None:
                    ui.button(str(primary_label), on_click=on_primary).props("dense")
                if secondary_label and on_secondary is not None:
                    ui.button(str(secondary_label), on_click=on_secondary).props("outline dense")


def render_error_block(
    *,
    title: str,
    message: str | None = None,
    retry_label: str | None = None,
    on_retry: Any | None = None,
) -> None:
    """Render a consistent error-state block with optional retry action."""
    with ui.card().classes("lp-card w-full"):
        ui.label(str(title or "")).classes("text-sm")
        ui.label(str(message or "Unexpected error")).classes("text-sm").style("color: var(--lp-muted)")
        if retry_label and on_retry is not None:
            with ui.row().classes("items-center gap-2 mt-2"):
                ui.button(str(retry_label), on_click=on_retry).props("outline dense")
