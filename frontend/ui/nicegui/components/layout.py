from __future__ import annotations


"""Shared layout components for the NiceGUI frontend."""

from nicegui import ui

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.config import settings
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.session_store import SessionStore


def render_shell(*, title: str, store: SessionStore, api: ApiClient) -> None:
    """Render the global header with navigation and logout.

    Args:
        title: Page title to show in the header.
        store: Session store.
        api: API client.
    """
    user = store.get_user() or {}
    is_admin = str(user.get("role") or "") == "admin"
    current_path = str(getattr(getattr(ui.context.client, "page", None), "path", "") or "")

    def _is_active(target: str) -> bool:
        return current_path == target

    with ui.header().classes("lp-header items-center justify-between"):
        ui.label(title).classes("text-lg font-semibold")
        with ui.row().classes("items-center gap-2"):
            # A compact menu keeps navigation usable on small screens.
            with ui.dropdown_button("Menu", icon="menu", auto_close=True).props("outline dense"):
                home_item = ui.menu_item("Home", on_click=lambda: ui.navigate.to("/"))
                if _is_active("/"):
                    home_item.classes("lp-nav-active")

                if settings.feature_ai_curator:
                    ai_item = ui.menu_item("AI Curator", on_click=lambda: ui.navigate.to("/ai"))
                    if _is_active("/ai"):
                        ai_item.classes("lp-nav-active")

                courses_item = ui.menu_item("Courses", on_click=lambda: ui.navigate.to("/courses"))
                if _is_active("/courses"):
                    courses_item.classes("lp-nav-active")

                my_courses_item = ui.menu_item("My Courses", on_click=lambda: ui.navigate.to("/courses/my"))
                if _is_active("/courses/my"):
                    my_courses_item.classes("lp-nav-active")

                paths_item = ui.menu_item("Paths", on_click=lambda: ui.navigate.to("/paths"))
                if _is_active("/paths"):
                    paths_item.classes("lp-nav-active")

                my_paths_item = ui.menu_item("My Paths", on_click=lambda: ui.navigate.to("/paths/my"))
                if _is_active("/paths/my"):
                    my_paths_item.classes("lp-nav-active")

                if settings.feature_articles:
                    articles_item = ui.menu_item("Articles", on_click=lambda: ui.navigate.to("/articles"))
                    if _is_active("/articles"):
                        articles_item.classes("lp-nav-active")
                if is_admin:
                    ui.separator()
                    admin_item = ui.menu_item("Admin", on_click=lambda: ui.navigate.to("/admin/users"))
                    if _is_active("/admin/users"):
                        admin_item.classes("lp-nav-active")

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
