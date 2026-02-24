from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from backend.services.auth_service import AuthService


def require_row_exists(row: dict[str, Any] | None) -> dict[str, Any]:
    """Return row or raise 404 when missing."""
    if not row:
        raise HTTPException(status_code=404, detail="not_found")
    return row


def require_row_parent_match(*, row: dict[str, Any], parent_field: str, parent_id: int) -> None:
    """Raise 404 when a child row does not belong to the expected parent id."""
    try:
        row_parent_id = int(row.get(parent_field) or 0)
    except (TypeError, ValueError):
        row_parent_id = 0
    if row_parent_id != int(parent_id):
        raise HTTPException(status_code=404, detail="not_found")


async def require_owner_or_admin(
    *,
    row: dict[str, Any],
    current_user: str,
    auth: AuthService,
    owner_field: str = "created_by",
) -> None:
    """Raise 403 unless the current user is admin or matches the owner field."""
    if await auth.is_admin(current_user):
        return
    owner = str(row.get(owner_field) or "")
    if owner != str(current_user):
        raise HTTPException(status_code=403, detail="forbidden")


async def require_existing_owner_or_admin(
    *,
    row: dict[str, Any] | None,
    current_user: str,
    auth: AuthService,
    owner_field: str = "created_by",
) -> dict[str, Any]:
    """Ensure row exists and current user is owner/admin, returning the row."""
    existing = require_row_exists(row)
    await require_owner_or_admin(row=existing, current_user=current_user, auth=auth, owner_field=owner_field)
    return existing
