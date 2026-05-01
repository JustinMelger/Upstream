from __future__ import annotations

from pathlib import Path

import pytest


@pytest.mark.unit
def test_shared_card_frame_helpers_exist() -> None:
    src = Path("frontend/ui/nicegui/components/card_frame.py").read_text(encoding="utf-8")
    assert "def render_card_topright" in src
    assert "def render_card_main_row" in src
    assert "def render_card_content_column" in src
    assert "def render_card_actions_row" in src


@pytest.mark.unit
def test_courses_card_uses_shared_card_frame_helpers() -> None:
    src = Path("frontend/ui/nicegui/domains/courses/sections.py").read_text(encoding="utf-8")
    assert "render_card_topright" in src
    assert "render_card_main_row" in src
    assert "render_card_content_column" in src
    assert "render_card_actions_row" in src


@pytest.mark.unit
def test_paths_card_uses_shared_card_frame_helpers() -> None:
    src = Path("frontend/ui/nicegui/components/path_card.py").read_text(encoding="utf-8")
    assert "render_card_topright" in src
    assert "render_card_content_column" in src
    assert "render_card_actions_row" in src


@pytest.mark.unit
def test_articles_card_uses_shared_card_frame_helpers() -> None:
    src = Path("frontend/ui/nicegui/domains/articles/sections.py").read_text(encoding="utf-8")
    assert "render_card_topright" in src
    assert "render_card_main_row" in src
    assert "render_card_content_column" in src
    assert "render_card_actions_row" in src


@pytest.mark.unit
def test_courses_and_articles_topbar_are_componentized_in_sections() -> None:
    courses_src = Path("frontend/ui/nicegui/domains/courses/sections.py").read_text(encoding="utf-8")
    articles_src = Path("frontend/ui/nicegui/domains/articles/sections.py").read_text(encoding="utf-8")
    assert "render_courses_topbar(" in courses_src
    assert "render_articles_topbar(" in articles_src


@pytest.mark.unit
def test_load_more_footer_component_is_reused_across_pages() -> None:
    pagination_src = Path("frontend/ui/nicegui/components/pagination.py").read_text(encoding="utf-8")
    paths_sections_src = Path("frontend/ui/nicegui/domains/paths/sections.py").read_text(encoding="utf-8")
    articles_sections_src = Path("frontend/ui/nicegui/domains/articles/sections.py").read_text(encoding="utf-8")
    courses_sections_src = Path("frontend/ui/nicegui/domains/courses/sections.py").read_text(encoding="utf-8")
    assert "def render_load_more_footer" in pagination_src
    assert "render_load_more_footer(" in paths_sections_src
    assert "render_load_more_footer(" in articles_sections_src
    assert "render_load_more_footer(" in courses_sections_src


@pytest.mark.unit
def test_course_primary_action_awaits_async_callbacks() -> None:
    src = Path("frontend/ui/nicegui/domains/courses/sections.py").read_text(encoding="utf-8")
    assert "await ctx.actions.on_view()" in src
    assert "await ctx.actions.on_review()" in src
