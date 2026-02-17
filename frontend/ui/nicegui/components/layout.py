from __future__ import annotations


"""Shared layout components for the NiceGUI frontend."""

from collections.abc import Callable

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

    with ui.header().classes("lp-header"):
        # Keep header content aligned with `.lp-container` so page facets/cards
        # visually line up with the page title.
        with ui.row().classes("lp-header-inner"):
            ui.label(title).classes("text-lg font-semibold")
            with ui.row().classes("items-center gap-2"):
                # A compact menu keeps navigation usable on small screens.
                with ui.dropdown_button("Menu", icon="menu", auto_close=True).props("outline dense"):
                    home_item = ui.menu_item("Insights", on_click=lambda: ui.navigate.to("/insights"))
                    if _is_active("/insights"):
                        home_item.classes("lp-nav-active")

                    learning_item = ui.menu_item("My learning", on_click=lambda: ui.navigate.to("/learning"))
                    if _is_active("/learning"):
                        learning_item.classes("lp-nav-active")

                    if settings.feature_ai_curator:
                        ai_item = ui.menu_item("AI Curator", on_click=lambda: ui.navigate.to("/ai"))
                        if _is_active("/ai"):
                            ai_item.classes("lp-nav-active")

                    courses_item = ui.menu_item("Courses", on_click=lambda: ui.navigate.to("/courses"))
                    if _is_active("/courses"):
                        courses_item.classes("lp-nav-active")

                    paths_item = ui.menu_item("Paths", on_click=lambda: ui.navigate.to("/paths"))
                    if _is_active("/paths"):
                        paths_item.classes("lp-nav-active")

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


def render_split_layout(*, rail: Callable[[], None], main: Callable[[], None], rail_classes: str = "") -> None:
    """Render a reusable rail + main split layout.

    Args:
        rail: Function that renders the left rail content.
        main: Function that renders the main content area.
        rail_classes: Optional additional CSS classes for the rail container.
    """
    with ui.element("div").classes("lp-split"):
        with ui.element("aside").classes(f"lp-rail {rail_classes}".strip()):
            with ui.element("div").classes("lp-rail-content"):
                rail()
        with ui.element("div").classes("lp-main"):
            main()
