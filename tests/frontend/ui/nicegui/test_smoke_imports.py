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
        home,
        learning,
        login,
    )

    for mod in [ai_curator, admin_users, home, learning, login]:
        assert callable(getattr(mod, "register", None))


@pytest.mark.unit
def test_paths_component_modules_are_importable() -> None:
    from frontend.ui.nicegui.components import path_card, path_detail_sections, paths_sections

    assert callable(getattr(path_card, "render_path_card", None))
    assert callable(getattr(path_detail_sections, "render_path_detail_header", None))
    assert callable(getattr(path_detail_sections, "render_path_detail_learning_section", None))
    assert callable(getattr(paths_sections, "render_paths_topbar", None))
    assert callable(getattr(paths_sections, "render_paths_filter_rail", None))
