"""Root route redirects."""

from __future__ import annotations

from nicegui import ui
from starlette.responses import RedirectResponse

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.session_store import SessionStore


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register root redirects."""
    _ = store
    _ = api

    @ui.page("/")
    async def root_page() -> RedirectResponse:
        """Default app landing route: redirect to Login."""
        return RedirectResponse("/login")
