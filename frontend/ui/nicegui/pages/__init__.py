"""NiceGUI pages package.

This package exposes individual modules (each providing `register(...)`) that
wire `@ui.page` routes.
"""

from importlib import import_module
from types import ModuleType


__all__ = [
    "ai_curator",
    "admin_users",
    "activity",
    "articles",
    "courses",
    "explore",
    "home",
    "learning",
    "login",
    "paths",
    "profile",
    "share",
    "teams",
]


def __getattr__(name: str) -> ModuleType:
    if name in __all__:
        return import_module(f"{__name__}.{name}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
