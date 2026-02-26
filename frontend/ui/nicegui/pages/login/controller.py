"""Controller workflows for the Login page."""

from __future__ import annotations

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.core.session_store import SessionStore


class LoginPageController:
    """Imperative auth workflows for `/login`."""

    def __init__(self, *, store: SessionStore, api: ApiClient):
        """Initialize the controller.

        Args:
            store: Session store for token persistence.
            api: Shared API client.

        """
        self._store = store
        self._api = api

    def is_authenticated(self) -> bool:
        """Return whether current session has an auth token."""
        return bool(self._store.get_token())

    async def submit_login(self, *, username: str, password: str) -> None:
        """Authenticate and persist session token."""
        await self._store.login(self._api, username=str(username or ""), password=str(password or ""))
