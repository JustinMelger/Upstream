from __future__ import annotations


"""Shared layout components for the NiceGUI frontend."""

from nicegui import ui

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.session_store import SessionStore


def render_shell(*, title: str, store: SessionStore, api: ApiClient) -> None:
    """Render the global header with navigation and logout.

    Args:
        title: Page title to show in the header.
        store: Session store.
        api: API client.
    """
    with ui.header().classes("lp-header items-center justify-between"):
        ui.label(title).classes("text-lg font-semibold")
        with ui.row().classes("items-center gap-2"):
            # A compact menu keeps navigation usable on small screens.
            with ui.dropdown_button("Menu", icon="menu", auto_close=True).props("outline dense"):
                ui.menu_item("Home", on_click=lambda: ui.navigate.to("/"))
                ui.menu_item("AI Curator", on_click=lambda: ui.navigate.to("/ai"))
                ui.menu_item("Courses", on_click=lambda: ui.navigate.to("/courses"))
                ui.menu_item("My Courses", on_click=lambda: ui.navigate.to("/courses/my"))
                ui.menu_item("Paths", on_click=lambda: ui.navigate.to("/paths"))
                ui.menu_item("My Paths", on_click=lambda: ui.navigate.to("/paths/my"))
                ui.separator()
                ui.menu_item("Admin", on_click=lambda: ui.navigate.to("/admin/users"))

            @guard_ui_action(title="Logout failed")
            async def _logout() -> None:
                await store.logout(api)
                ui.navigate.to("/login")

            ui.button("Logout", on_click=_logout).props("outline dense")


def render_container() -> ui.column:
    """Return a centered page container for content.

    Returns:
        A NiceGUI column with the app container styles applied.
    """
    return ui.column().classes("lp-container")
