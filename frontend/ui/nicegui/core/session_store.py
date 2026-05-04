from __future__ import annotations


"""Session state for the NiceGUI frontend.

`SessionStore` persists state in `nicegui.app.storage.user`, which is per-browser
session storage managed by NiceGUI. This stores:

- The current `X-Session-Token`.
- The current `/auth/me` payload (username/role).
"""

from typing import Any

from nicegui import app

from frontend.ui.nicegui.core.api_client import ApiClient, ApiError


class SessionStore:
    """Stores session token and current user in NiceGUI user storage."""

    _TOKEN_KEY = "session_token"
    _USER_KEY = "current_user"

    def get_token(self) -> str | None:
        """Return the current session token."""
        return app.storage.user.get(self._TOKEN_KEY)

    def set_token(self, token: str | None) -> None:
        """Set or clear the current session token.

        Args:
            token: Token to store, or `None` to clear it.
        """
        current_token = app.storage.user.get(self._TOKEN_KEY)
        if current_token != token:
            app.storage.user.pop(self._USER_KEY, None)
        if token:
            app.storage.user[self._TOKEN_KEY] = token
        else:
            app.storage.user.pop(self._TOKEN_KEY, None)

    def clear(self) -> None:
        """Clear token and cached user info."""
        app.storage.user.pop(self._TOKEN_KEY, None)
        app.storage.user.pop(self._USER_KEY, None)

    def get_user(self) -> dict[str, Any] | None:
        """Return the cached `/auth/me` user payload, if present."""
        value = app.storage.user.get(self._USER_KEY)
        return value if isinstance(value, dict) else None

    def set_user(self, user: dict[str, Any] | None) -> None:
        """Set or clear the cached `/auth/me` user payload.

        Args:
            user: User payload dict, or `None` to clear it.
        """
        if user:
            app.storage.user[self._USER_KEY] = user
        else:
            app.storage.user.pop(self._USER_KEY, None)

    async def login(self, api: ApiClient, *, username: str, password: str) -> dict[str, Any]:
        """Login and persist token and user.

        Args:
            api: API client.
            username: Username to authenticate.
            password: Password to authenticate.

        Returns:
            The `/auth/me` payload.

        Raises:
            ApiError: If authentication fails or the backend response is invalid.
        """
        previous_token = self.get_token()
        previous_user = self.get_user()
        self.clear()
        try:
            payload = await api.post("/auth/login", {"username": username, "password": password}, token_override="")
        except ApiError:
            self.set_token(previous_token)
            self.set_user(previous_user)
            raise
        token = str(payload.get("token") or "")
        if not token:
            self.set_token(previous_token)
            self.set_user(previous_user)
            raise ApiError(status_code=500, message="missing_token")
        self.set_token(token)
        try:
            me_raw = await api.get("/auth/me")
        except ApiError:
            self.set_token(previous_token)
            self.set_user(previous_user)
            raise
        if not isinstance(me_raw, dict):
            self.set_token(previous_token)
            self.set_user(previous_user)
            raise ApiError(status_code=500, message="invalid_auth_me_payload")
        me: dict[str, Any] = dict(me_raw)
        self.set_user(me)
        return me

    async def logout(self, api: ApiClient) -> None:
        """Logout and clear local state.

        Args:
            api: API client.
        """
        try:
            await api.post("/auth/logout", {}, token_override=None)
        except ApiError:
            pass
        self.clear()
