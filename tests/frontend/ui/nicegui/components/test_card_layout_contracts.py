from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.unit
def test_courses_card_uses_bottom_action_row_not_right_column() -> None:
    src = Path("frontend/ui/nicegui/pages/courses/sections.py").read_text(encoding="utf-8")
    assert 'with ui.element("div").classes("lp-card-topright")' in src
    assert 'with ui.row().classes("items-center gap-2 mt-2")' in src
    # Regression guard: old layout used a separate right-aligned column which collapsed on short cards.
    assert 'with ui.column().classes("items-end gap-2")' not in src


@pytest.mark.unit
def test_paths_card_keeps_topright_badges_and_bottom_actions() -> None:
    src = Path("frontend/ui/nicegui/components/path_card.py").read_text(encoding="utf-8")
    assert 'with ui.element("div").classes("lp-card-topright")' in src
    assert 'with ui.row().classes("items-center gap-2 mt-2")' in src


@pytest.mark.unit
def test_articles_card_keeps_topright_badge_and_bottom_actions() -> None:
    src = Path("frontend/ui/nicegui/pages/articles/sections.py").read_text(encoding="utf-8")
    assert 'with ui.element("div").classes("lp-card-topright")' in src
    assert 'with ui.row().classes("items-center gap-2 mt-2")' in src


@pytest.mark.unit
def test_courses_and_articles_topbar_are_componentized_in_sections() -> None:
    courses_src = Path("frontend/ui/nicegui/pages/courses/page.py").read_text(encoding="utf-8")
    articles_src = Path("frontend/ui/nicegui/pages/articles/page.py").read_text(encoding="utf-8")
    assert "render_courses_topbar(" in courses_src
    assert "render_articles_topbar(" in articles_src


@pytest.mark.unit
def test_load_more_footer_component_is_reused_across_pages() -> None:
    pagination_src = Path("frontend/ui/nicegui/components/pagination.py").read_text(encoding="utf-8")
    paths_src = Path("frontend/ui/nicegui/pages/paths/page.py").read_text(encoding="utf-8")
    articles_sections_src = Path("frontend/ui/nicegui/pages/articles/sections.py").read_text(encoding="utf-8")
    courses_sections_src = Path("frontend/ui/nicegui/pages/courses/sections.py").read_text(encoding="utf-8")
    assert "def render_load_more_footer" in pagination_src
    assert "render_load_more_footer(" in paths_src
    assert "render_load_more_footer(" in articles_sections_src
    assert "render_load_more_footer(" in courses_sections_src
