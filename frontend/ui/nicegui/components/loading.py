"""Shared loading UI helpers for NiceGUI pages."""

from __future__ import annotations

from nicegui import ui


def render_card_skeletons(*, count: int = 4) -> None:
    """Render a simple list of skeleton cards.

    Args:
        count: Number of placeholder cards.
    """
    for _ in range(max(1, int(count))):
        with ui.card().classes("w-full"):
            with ui.row().classes("items-center justify-between w-full"):
                with ui.column().classes("gap-2 grow"):
                    ui.skeleton(type="text").classes("w-2/3")
                    ui.skeleton(type="text").classes("w-1/2")
                with ui.row().classes("items-center gap-2"):
                    ui.skeleton(type="QBtn", width="84px", height="36px")
                    ui.skeleton(type="QBtn", width="84px", height="36px")


def render_inline_spinner(*, label: str = "Loading…") -> None:
    """Render a compact spinner + label row."""
    with ui.row().classes("items-center gap-2"):
        ui.spinner(size="sm")
        ui.label(label).classes("text-sm text-gray-600")
