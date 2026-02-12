"""NiceGUI pages package.

This package exposes individual modules (each providing `register(...)`) that
wire `@ui.page` routes.
"""

from frontend.ui.nicegui.pages import ai_curator, admin_users, courses, home, login, my_courses, my_paths, paths, placeholders


__all__ = [
    "ai_curator",
    "admin_users",
    "courses",
    "home",
    "login",
    "my_courses",
    "my_paths",
    "paths",
    "placeholders",
]

