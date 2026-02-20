"""Pure helper functions for Login page."""

from __future__ import annotations


def normalize_credentials(*, username: str, password: str) -> tuple[str, str]:
    """Normalize username/password values from input fields."""
    return str(username or "").strip(), str(password or "")


def credentials_valid(*, username: str, password: str) -> bool:
    """Return whether normalized credentials are valid for submit."""
    u, p = normalize_credentials(username=username, password=password)
    return bool(u and p)
