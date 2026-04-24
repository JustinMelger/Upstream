"""Root route redirects."""

from __future__ import annotations

from nicegui import ui

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.session_store import SessionStore


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register root redirects."""
    _ = store
    _ = api

    @ui.page("/")
    async def root_page() -> None:
        """Default app landing route: redirect to Home."""
        ui.navigate.to("/home")
