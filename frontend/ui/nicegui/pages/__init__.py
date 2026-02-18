"""NiceGUI pages package.

This package exposes individual modules (each providing `register(...)`) that
wire `@ui.page` routes.
"""

from frontend.ui.nicegui.pages import (
    activity,
    admin_users,
    ai_curator,
    articles,
    courses,
    home,
    learning,
    login,
    paths,
    placeholders,
    timeline,
)


__all__ = [
    "ai_curator",
    "admin_users",
    "activity",
    "articles",
    "courses",
    "home",
    "learning",
    "login",
    "paths",
    "placeholders",
    "timeline",
]
