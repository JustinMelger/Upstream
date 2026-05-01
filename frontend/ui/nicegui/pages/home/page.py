"""Root route redirects."""

from __future__ import annotations

from nicegui import ui

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register root redirects."""
    _ = store
    _ = api

    @ui.page("/")
    async def root_page() -> None:
        """Default app landing route: redirect to Home."""
        user = await require_user(store, api)
        if user is None:
            return
        ui.navigate.to("/home")
