"""Admin users page orchestration for the NiceGUI frontend."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

from frontend.ui.nicegui.core.api_client import ApiClient


async def list_users(*, api: ApiClient) -> list[dict[str, Any]]:
    """Load users from backend."""
    rows = await api.get("/auth/users")
    return [row for row in list(rows or []) if isinstance(row, dict)]


async def create_user(*, api: ApiClient, username: str, password: str, role: str) -> None:
    """Create a new user."""
    await api.post("/auth/users", {"username": str(username), "password": str(password), "role": str(role)})


async def reset_password(*, api: ApiClient, username: str, password: str) -> None:
    """Reset user password."""
    await api.post("/auth/users/reset", {"username": str(username), "password": str(password)})


async def delete_user(*, api: ApiClient, username: str) -> None:
    """Delete a user."""
    encoded = quote(str(username or "").strip(), safe="")
    await api.delete(f"/auth/users/{encoded}")


async def set_disabled(*, api: ApiClient, username: str, disabled: bool) -> None:
    """Disable/enable a user."""
    await api.post("/auth/users/disable", {"username": str(username), "disabled": bool(disabled)})

