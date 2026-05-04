from __future__ import annotations

"""NiceGUI application composition.

This module wires together core utilities (`ApiClient`, `SessionStore`) and
registers all `@ui.page` routes.
"""

from nicegui import app, core, ui

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.config import settings
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.core.theme import apply_theme
from frontend.ui.nicegui.pages import (
    admin_users,
    ai_curator,
    explore,
    home,
    learning,
    login,
    profile,
    share,
    teams,
)


def create_app() -> None:
    """Register all NiceGUI routes and apply global theme."""
    apply_theme()
    store = SessionStore()
    api = ApiClient(base_url=settings.backend_url, token_provider=store.get_token)
    app.on_shutdown(api.aclose)

    login.register(store=store, api=api)
    home.register(store=store, api=api)
    explore.register(store=store, api=api)
    learning.register(store=store, api=api)
    teams.register(store=store, api=api)
    profile.register(store=store, api=api)
    share.register(store=store, api=api)
    if settings.feature_ai_curator:
        ai_curator.register(store=store, api=api)
    admin_users.register(store=store, api=api)


def main() -> None:
    """Start the NiceGUI ASGI server."""
    create_app()
    core.app.config.socket_io_js_transports = list(settings.socket_transports)
    core.sio.eio.max_http_buffer_size = max(1_000_000, int(settings.websocket_max_bytes))
    ui.run(
        host=settings.host,
        port=settings.port,
        title="Learning Hub",
        reload=settings.reload,
        reconnect_timeout=settings.reconnect_timeout_s,
        show=settings.show,
        storage_secret=settings.storage_secret,
        message_history_length=max(0, int(settings.message_history_length)),
    )


if __name__ in {"__main__", "__mp_main__"}:
    main()
