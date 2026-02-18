"""Paths page package (MVC layout)."""

from frontend.ui.nicegui.pages.paths.page import (
    _normalize_path_view_mode,
    _path_matches_state,
    register,
)


__all__ = [
    "register",
    "_normalize_path_view_mode",
    "_path_matches_state",
]
