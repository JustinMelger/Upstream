from __future__ import annotations

from frontend.ui.nicegui.core.feed_copy import (
    activity_empty_description,
    format_count_label,
    format_explore_scope_text,
    format_learning_inventory_text,
    team_activity_empty_description,
)


def test_format_count_label_handles_singular_and_plural() -> None:
    assert format_count_label(count=1, singular="path") == "1 path"
    assert format_count_label(count=2, singular="path") == "2 paths"


def test_format_learning_inventory_text_uses_learning_items_and_paths() -> None:
    assert format_learning_inventory_text(learning_item_count=3, path_count=1) == "3 learning items · 1 path"


def test_format_explore_scope_text_uses_learning_item_umbrella_for_all_tab() -> None:
    assert (
        format_explore_scope_text(tab_value="courses", course_count=3, video_count=2, article_count=5, path_count=8)
        == "3 courses"
    )
    assert (
        format_explore_scope_text(tab_value="videos", course_count=3, video_count=2, article_count=5, path_count=8)
        == "2 videos"
    )
    assert (
        format_explore_scope_text(tab_value="articles", course_count=3, video_count=2, article_count=5, path_count=8)
        == "5 articles"
    )
    assert (
        format_explore_scope_text(tab_value="paths", course_count=3, video_count=2, article_count=5, path_count=8) == "8 paths"
    )
    assert (
        format_explore_scope_text(tab_value="all", course_count=3, video_count=2, article_count=5, path_count=8)
        == "10 learning items | 8 paths"
    )


def test_activity_and_team_empty_copy_use_learning_item_language() -> None:
    assert activity_empty_description(current_tab="team") == (
        "When teammates share, recommend, or rate learning items and paths, updates will appear here."
    )
    assert activity_empty_description(current_tab="inbox") == (
        "When teammates review or recommend your shared learning items and paths, updates will appear here."
    )
    assert team_activity_empty_description() == "Share a learning item or path to start activity in this feed."
