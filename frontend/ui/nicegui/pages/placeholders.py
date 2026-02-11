"""Placeholder module for future NiceGUI pages.

This keeps the import surface stable while routes are still being added.
"""

from __future__ import annotations

from nicegui import ui

from frontend.ui.nicegui.components.layout import render_shell
from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.guards import require_user
from frontend.ui.nicegui.core.session_store import SessionStore


def register(*, store: SessionStore, api: ApiClient) -> None:
    """Register placeholder routes.

    Args:
        store: Session store.
        api: API client.
    """
    # Placeholder module retained for future pages.
    return None
