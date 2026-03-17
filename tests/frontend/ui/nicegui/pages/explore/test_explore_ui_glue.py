from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.explore.ui_glue import compute_explore_meta_text, normalize_tab, TAB_OPTIONS


@pytest.mark.unit
def test_normalize_tab_accepts_paths() -> None:
    assert normalize_tab("paths") == "paths"
    assert normalize_tab("PATHS") == "paths"
    assert normalize_tab("invalid") == "all"


@pytest.mark.unit
def test_tab_options_include_paths() -> None:
    assert TAB_OPTIONS == {
        "all": "All",
        "courses": "Courses",
        "videos": "Videos",
        "paths": "Paths",
        "articles": "Articles",
    }


@pytest.mark.unit
def test_compute_explore_meta_text_counts_by_active_tab() -> None:
    assert compute_explore_meta_text(tab_value="courses", course_count=3, video_count=2, path_count=8, article_count=5) == "3 courses"
    assert compute_explore_meta_text(tab_value="videos", course_count=3, video_count=2, path_count=8, article_count=5) == "2 videos"
    assert compute_explore_meta_text(tab_value="paths", course_count=3, video_count=2, path_count=8, article_count=5) == "8 paths"
    assert compute_explore_meta_text(tab_value="articles", course_count=3, video_count=2, path_count=8, article_count=5) == "5 articles"
    assert compute_explore_meta_text(tab_value="all", course_count=3, video_count=2, path_count=8, article_count=5) == "10 learning items | 8 paths"
