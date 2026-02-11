from __future__ import annotations


"""Route guards for the NiceGUI frontend.

NiceGUI pages are regular Python functions decorated with `@ui.page`. Any
exceptions raised during rendering can surface as 500 pages. These guards
prefer "redirect + return None" to keep failures user-friendly.
"""

from typing import Any

from nicegui import ui

from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.session_store import SessionStore


async def require_user(store: SessionStore, api: ApiClient, *, require_admin: bool = False) -> dict[str, Any] | None:
    """Ensure the user is logged in (and optionally admin).

    If unauthenticated, this function redirects to `/login` and returns `None`.
    If `require_admin=True` and the user is not an admin, it redirects to `/`.

    Args:
        store: Session store.
        api: API client.
        require_admin: Whether to enforce admin role.

    Returns:
        The current user dict when authenticated, otherwise `None` after redirecting.
    """
    token = store.get_token()
    if not token:
        ui.navigate.to("/login")
        return None

    user = store.get_user()
    if not user:
        try:
            user = await api.get("/auth/me")
            store.set_user(user)
        except ApiError:
            store.clear()
            ui.navigate.to("/login")
            return None

    if require_admin and str(user.get("role") or "") != "admin":
        ui.navigate.to("/")
        return None

    return user
