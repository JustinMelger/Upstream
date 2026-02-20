"""Reusable pagination UI components."""

from __future__ import annotations

from typing import Any

from nicegui import ui


def render_load_more_footer(*, shown_page_count: int, shown_total_count: int, on_load_more: Any) -> None:
    """Render a standard load-more footer when not all rows are visible."""
    if int(shown_total_count) <= int(shown_page_count):
        return
    with ui.row().classes("items-center justify-center mt-2"):
        ui.button(f"Load more ({int(shown_page_count)}/{int(shown_total_count)})", on_click=on_load_more).props("outline")
