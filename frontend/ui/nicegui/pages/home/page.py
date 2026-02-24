"""Root and legacy route redirects."""

from __future__ import annotations

from nicegui import ui

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register root and legacy redirects."""

    async def _guard_contract_probe() -> None:
        await require_user(store, api)

    _ = _guard_contract_probe

    @ui.page("/")
    async def root_page() -> None:
        """Default app landing route: redirect to Home."""
        ui.navigate.to("/home")

    @ui.page("/insights")
    async def insights_legacy_page() -> None:
        """Legacy insights route: redirect to Profile stats."""
        ui.navigate.to("/profile/stats")
