"""AI curator page package exports."""

from __future__ import annotations

from typing import Any


def register(*args: Any, **kwargs: Any) -> None:
    """Lazy register proxy to avoid import cycles during utility imports."""
    from frontend.ui.nicegui.pages.ai_curator.page import register as _register

    _register(*args, **kwargs)


__all__ = ["register"]
