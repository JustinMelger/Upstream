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

