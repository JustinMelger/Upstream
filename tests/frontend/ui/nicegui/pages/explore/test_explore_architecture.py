from __future__ import annotations

from pathlib import Path

import pytest


_EXPLORE_DIR = Path("frontend/ui/nicegui/pages/explore")


@pytest.mark.unit
def test_explore_learning_item_rows_use_shared_browse_row_renderer() -> None:
    src = (_EXPLORE_DIR / "list_items.py").read_text(encoding="utf-8")
    assert "def _render_browse_row(" in src
    assert "render_article_card(" not in src


@pytest.mark.unit
def test_explore_detail_path_uses_unselect_endpoint_for_untracking() -> None:
    src = (_EXPLORE_DIR / "detail_path.py").read_text(encoding="utf-8")
    assert 'api.post(f"/paths/{pid}/unselect", {})' in src
    assert 'api.delete(f"/paths/{pid}/select")' not in src


@pytest.mark.unit
def test_explore_detail_path_reuses_shared_tracking_seed_helper_for_select() -> None:
    src = (_EXPLORE_DIR / "detail_path.py").read_text(encoding="utf-8")
    assert "select_path_and_seed_tracking(" in src


@pytest.mark.unit
def test_explore_detail_course_refreshes_route_after_tracking_mutations() -> None:
    src = (_EXPLORE_DIR / "detail_course.py").read_text(encoding="utf-8")
    assert 'refresh_url = f"/explore/courses/{cid}"' in src
    assert "ui.navigate.to(refresh_url)" in src
    assert 'if normalized_status == "interested":' in src


@pytest.mark.unit
def test_explore_detail_review_summaries_refresh_after_review_mutations() -> None:
    for filename in ["detail_course.py", "detail_article.py", "detail_video.py", "detail_path.py"]:
        src = (_EXPLORE_DIR / filename).read_text(encoding="utf-8")
        assert "on_changed=_handle_reviews_changed" in src


@pytest.mark.unit
def test_explore_detail_close_actions_return_to_matching_tab() -> None:
    common_src = (_EXPLORE_DIR / "detail_common.py").read_text(encoding="utf-8")
    assert 'back_url: str = "/explore"' in common_src
    assert 'ui.link("Explore", str(back_url or "/explore"))' in common_src

    assert 'render_breadcrumb(label="Courses", back_url="/explore?tab=courses")' in (
        _EXPLORE_DIR / "detail_course.py"
    ).read_text(encoding="utf-8")
    assert 'render_breadcrumb(label="Articles", back_url="/explore?tab=articles")' in (
        _EXPLORE_DIR / "detail_article.py"
    ).read_text(encoding="utf-8")
    assert 'render_breadcrumb(label="Videos", back_url="/explore?tab=videos")' in (_EXPLORE_DIR / "detail_video.py").read_text(
        encoding="utf-8"
    )
    assert 'render_breadcrumb(label="Learning Path", back_url="/explore?tab=paths")' in (
        _EXPLORE_DIR / "detail_path.py"
    ).read_text(encoding="utf-8")


@pytest.mark.unit
def test_explore_article_resource_link_opens_in_new_tab() -> None:
    src = (_EXPLORE_DIR / "detail_article.py").read_text(encoding="utf-8")
    assert 'ui.link(learning_item_source_action_label("article"), source_url).props("target=_blank")' in src
