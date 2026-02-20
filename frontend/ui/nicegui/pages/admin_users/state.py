"""State model for the Admin Users page."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AdminUsersPageState:
    """Mutable UI state for `/admin/users`."""

    users: list[dict[str, Any]] = field(default_factory=list)
    loading: bool = False
