"""UI sections/constants for Admin Users page."""

from __future__ import annotations


USERS_TABLE_COLUMNS: list[dict[str, str]] = [
    {"name": "username", "label": "Username", "field": "username"},
    {"name": "role", "label": "Role", "field": "role"},
    {"name": "created_at", "label": "Created at", "field": "created_at"},
    {"name": "updated_at", "label": "Updated at", "field": "updated_at"},
    {"name": "last_login_at", "label": "Last login", "field": "last_login_at"},
    {"name": "disabled", "label": "Disabled", "field": "disabled"},
]
