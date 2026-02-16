"""Reusable owner/admin kebab menu for card-level actions."""

from __future__ import annotations

from typing import Any, Callable

from nicegui import ui


def render_owner_menu(
    *,
    on_edit: Callable[..., Any],
    on_delete: Callable[..., Any],
    edit_label: str = "Edit",
    delete_label: str = "Delete",
) -> None:
    """Render a standard owner/admin action menu."""
    with ui.dropdown_button("", icon="more_vert", auto_close=True).props("dense flat"):
        ui.menu_item(edit_label, on_click=on_edit)
        ui.menu_item(delete_label, on_click=on_delete)
