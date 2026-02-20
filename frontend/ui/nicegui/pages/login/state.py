"""State model for the Login page."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class LoginPageState:
    """Mutable UI state for `/login`."""

    loading: bool = False
