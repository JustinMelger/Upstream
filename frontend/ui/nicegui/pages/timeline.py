"""Legacy timeline route redirecting into Insights tabs."""

from __future__ import annotations

from nicegui import ui

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.session_store import SessionStore


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register `/timeline` as a backward-compatible redirect."""

    @ui.page("/timeline")
    async def timeline_redirect_page() -> None:
        ui.navigate.to("/activity?tab=team")
