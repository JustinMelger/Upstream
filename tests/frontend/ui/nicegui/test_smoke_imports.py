"""Smoke tests for the NiceGUI frontend package.

These tests ensure modules are importable in CI without starting a server.
"""

from __future__ import annotations

import pytest


@pytest.mark.unit
def test_import_nicegui_main_module() -> None:
    from frontend.ui.nicegui import main as nicegui_main

    assert callable(getattr(nicegui_main, "create_app", None))
    assert callable(getattr(nicegui_main, "main", None))


@pytest.mark.unit
def test_pages_expose_register_callable() -> None:
    from frontend.ui.nicegui.pages import (
        admin_users,
        ai_curator,
        courses,
        home,
        learning,
        login,
        paths,
        placeholders,
    )

    for mod in [ai_curator, admin_users, courses, home, learning, login, paths, placeholders]:
        assert callable(getattr(mod, "register", None))
