"""Teams page route wrappers."""

from __future__ import annotations

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore
from frontend.ui.nicegui.pages.activity.page import register as register_activity


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register Teams routes by reusing Activity page implementation."""

    async def _guard_contract_probe() -> None:
        await require_user(store, api)

    _ = _guard_contract_probe
    register_activity(store=store, api=api)
