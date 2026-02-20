"""Controller workflows for the Admin Users page."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from frontend.ui.nicegui.core.api_client import ApiClient


class AdminUsersPageController:
    """Imperative API workflows for `/admin/users`."""

    def __init__(self, *, api: ApiClient):
        self._api = api

    async def list_users(self) -> list[dict[str, Any]]:
        """Load users from backend."""
        rows = await self._api.get("/auth/users")
        return [row for row in list(rows or []) if isinstance(row, dict)]

    async def create_user(self, *, username: str, password: str, role: str) -> None:
        """Create a new user."""
        await self._api.post("/auth/users", {"username": username, "password": password, "role": role})

    async def reset_password(self, *, username: str, password: str) -> None:
        """Reset user password."""
        await self._api.post("/auth/users/reset", {"username": username, "password": password})

    async def delete_user(self, *, username: str) -> None:
        """Delete a user."""
        encoded = quote(str(username or "").strip(), safe="")
        await self._api.delete(f"/auth/users/{encoded}")

    async def set_disabled(self, *, username: str, disabled: bool) -> None:
        """Disable/enable a user."""
        await self._api.post("/auth/users/disable", {"username": username, "disabled": bool(disabled)})
