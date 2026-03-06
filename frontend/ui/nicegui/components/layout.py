from __future__ import annotations


"""Shared layout components for the NiceGUI frontend."""

from collections.abc import Callable
from typing import Literal

from nicegui import ui

from frontend.ui.nicegui.core.a11y import apply_icon_button_a11y
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.config import settings
from frontend.ui.nicegui.core.errors import guard_ui_action
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.core.telemetry import track_ui_event_nowait


CatalogVariant = Literal["default", "courses", "articles", "paths", "explore"]


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

    def _is_path_prefix_active(prefix: str) -> bool:
        return current_path == prefix or current_path.startswith(f"{prefix}/")

    def _nav_click(*, label: str, target: str) -> None:
        track_ui_event_nowait(api=api, event_name="nav_click", context={"label": str(label), "target": str(target)})
        ui.navigate.to(target)

    with ui.header().classes("lp-header"):
        # Keep header content aligned with `.lp-container` so page facets/cards
        # visually line up with the page title.
        with ui.row().classes("lp-header-inner"):
            ui.label(title).classes("text-lg font-semibold")
            with ui.row().classes("items-center gap-2"):
                # A compact menu keeps navigation usable on small screens.
                with ui.dropdown_button("Menu", icon="menu", auto_close=True).props("outline dense"):
                    home_item = ui.menu_item("Home", on_click=lambda: _nav_click(label="home", target="/home"))
                    if _is_active("/home"):
                        home_item.classes("lp-nav-active")

                    explore_item = ui.menu_item("Explore", on_click=lambda: _nav_click(label="explore", target="/explore"))
                    if _is_active("/explore"):
                        explore_item.classes("lp-nav-active")

                    teams_item = ui.menu_item("Teams", on_click=lambda: _nav_click(label="teams", target="/teams"))
                    if _is_active("/teams"):
                        teams_item.classes("lp-nav-active")

                    profile_item = ui.menu_item("Profile", on_click=lambda: _nav_click(label="profile", target="/profile"))
                    if _is_path_prefix_active("/profile"):
                        profile_item.classes("lp-nav-active")

                    ui.separator()
                    if settings.feature_ai_curator:
                        ai_item = ui.menu_item("AI Curator", on_click=lambda: _nav_click(label="ai", target="/ai"))
                        if _is_path_prefix_active("/ai"):
                            ai_item.classes("lp-nav-active")
                    if is_admin:
                        ui.separator()
                        admin_item = ui.menu_item("Admin", on_click=lambda: _nav_click(label="admin", target="/admin/users"))
                        if _is_active("/admin/users"):
                            admin_item.classes("lp-nav-active")

                @guard_ui_action(title="Logout failed")
                async def _logout() -> None:
                    await store.logout(api)
                    ui.navigate.to("/login")

                activity_btn = apply_icon_button_a11y(
                    ui.button(
                        icon="markunread_mailbox",
                        on_click=lambda: _nav_click(label="teams", target="/teams"),
                    ).props("outline dense"),
                    label="Open teams inbox",
                    tooltip="Teams",
                )
                if _is_active("/teams"):
                    activity_btn.classes("lp-nav-active")

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


def render_catalog_scope(*, variant: CatalogVariant) -> ui.element:
    """Render a catalog theme scope so list pages can share layout but vary visual identity."""
    normalized: CatalogVariant = variant if variant in {"default", "courses", "articles", "paths", "explore"} else "default"
    return ui.element("section").classes(f"lp-catalog-scope lp-catalog--{normalized}")
