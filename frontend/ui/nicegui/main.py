from __future__ import annotations


"""NiceGUI application composition.

This module wires together core utilities (`ApiClient`, `SessionStore`) and
registers all `@ui.page` routes.
"""

from nicegui import ui

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.config import settings
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.core.theme import apply_theme
from frontend.ui.nicegui.pages import admin_users, ai_curator, courses, home, login, my_courses, my_paths, paths, placeholders


def create_app() -> None:
    """Register all NiceGUI routes and apply global theme."""
    apply_theme()
    store = SessionStore()
    api = ApiClient(base_url=settings.backend_url, token_provider=store.get_token)

    login.register(store=store, api=api)
    home.register(store=store, api=api)
    ai_curator.register(store=store, api=api)
    courses.register(store=store, api=api)
    paths.register(store=store, api=api)
    my_paths.register(store=store, api=api)
    my_courses.register(store=store, api=api)
    admin_users.register(store=store, api=api)
    placeholders.register(store=store, api=api)


def main() -> None:
    """Start the NiceGUI dev server."""
    create_app()
    ui.run(title="Learning Hub", reload=True, storage_secret=settings.storage_secret)


if __name__ in {"__main__", "__mp_main__"}:
    main()
