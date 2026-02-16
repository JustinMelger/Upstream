"""Route/module smoke checks for the NiceGUI frontend.

These tests avoid starting a NiceGUI server. They ensure our page modules remain
importable and expose `register(...)`.
"""

from __future__ import annotations

import importlib

import pytest


@pytest.mark.unit
def test_removed_legacy_pages_are_gone() -> None:
    """Legacy pages should not exist after IA consolidation."""
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("frontend.ui.nicegui.pages.my_courses")
    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("frontend.ui.nicegui.pages.my_paths")


@pytest.mark.unit
def test_all_page_modules_expose_register() -> None:
    from frontend.ui.nicegui import pages

    page_modules = [
        pages.admin_users,
        pages.ai_curator,
        pages.articles,
        pages.courses,
        pages.home,
        pages.learning,
        pages.login,
        pages.paths,
        pages.placeholders,
    ]
    for mod in page_modules:
        assert callable(getattr(mod, "register", None))
