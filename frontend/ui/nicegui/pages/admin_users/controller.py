"""Controller workflows for the Admin Users page."""

from __future__ import annotations

from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.services.admin_users_service import (
    create_user,
    delete_user,
    list_users,
    reset_password,
    set_disabled,
)


class AdminUsersPageController:
    """Imperative API workflows for `/admin/users`."""

    def __init__(self, *, api: ApiClient):
        """Initialize the controller.

        Args:
            api: Shared API client.

        """
        self._api = api

    async def list_users(self) -> list[dict[str, Any]]:
        """Load users from backend."""
        return await list_users(api=self._api)

    async def create_user(self, *, username: str, password: str, role: str) -> None:
        """Create a new user."""
        await create_user(api=self._api, username=username, password=password, role=role)

    async def reset_password(self, *, username: str, password: str) -> None:
        """Reset user password."""
        await reset_password(api=self._api, username=username, password=password)

    async def delete_user(self, *, username: str) -> None:
        """Delete a user."""
        await delete_user(api=self._api, username=username)

    async def set_disabled(self, *, username: str, disabled: bool) -> None:
        """Disable/enable a user."""
        await set_disabled(api=self._api, username=username, disabled=disabled)
