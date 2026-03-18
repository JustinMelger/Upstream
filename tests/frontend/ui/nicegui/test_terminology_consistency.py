from __future__ import annotations

from pathlib import Path


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_card_and_detail_action_labels_use_consistent_terms() -> None:
    path_card_src = _read("frontend/ui/nicegui/components/path_card.py")
    article_sections_src = _read("frontend/ui/nicegui/pages/articles/sections.py")
    course_sections_src = _read("frontend/ui/nicegui/pages/courses/sections.py")
    explore_course_detail_src = _read("frontend/ui/nicegui/pages/explore/detail_course.py")
    explore_article_detail_src = _read("frontend/ui/nicegui/pages/explore/detail_article.py")
    article_dialogs_src = _read("frontend/ui/nicegui/pages/articles/dialogs.py")

    assert 'ui.button("Open details"' in path_card_src
    assert 'ui.button("Open details"' in article_sections_src
    assert 'ui.menu_item("Open details"' in course_sections_src

    assert 'learning_item_source_action_label("course")' in explore_course_detail_src
    assert 'learning_item_source_action_label("article")' in explore_article_detail_src
    assert 'ui.button("Open source"' in article_dialogs_src

    # Prevent drift back to older mixed labels in key surfaces.
    assert 'ui.button("Select/Manage"' not in explore_course_detail_src
    assert 'ui.button("Select/Manage"' not in explore_article_detail_src
    assert 'ui.button("Open", on_click=view_action)' not in article_sections_src
    assert 'ui.button("Open", on_click=actions.on_view)' not in path_card_src
    assert 'ui.button("Manage in Paths"' not in _read("frontend/ui/nicegui/pages/explore/detail_path.py")
    assert 'ui.button("Open Path Workspace"' not in _read("frontend/ui/nicegui/pages/explore/detail_path.py")
    assert 'ui.menu_item("Details"' not in course_sections_src
    assert '"Open link"' not in article_dialogs_src
