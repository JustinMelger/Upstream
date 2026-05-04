from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from frontend.ui.nicegui.domains.courses import view_model


@pytest.mark.unit
def test_course_badge_formatters() -> None:
    assert view_model.format_rating_badge({"avg_rating": 4.5, "review_count": 2}) == "★ 4.5 (2)"
    assert view_model.format_rating_badge({"avg_rating": 4.5, "review_count": 0}) == ""


@pytest.mark.unit
def test_map_course_card_view_for_tracked_updated_course() -> None:
    now = datetime.now(timezone.utc)
    row = {
        "id": 5,
        "created_by": "admin",
        "created_at": (now - timedelta(days=3)).isoformat(),
        "updated_at": (now - timedelta(days=1)).isoformat(),
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    }
    tracked = {"status": "in_progress"}
    vm = view_model.map_course_card_view(
        course_row=row,
        tracked_row=tracked,
        review_summary_row={"avg_rating": 4.7, "review_count": 3},
    )
    assert vm.is_updated is True
    assert vm.is_new is False
    assert vm.card_class_suffix == " lp-course-card--in_progress"
    assert vm.shared_by == "admin"
    assert vm.rating_badge == "★ 4.7 (3)"
    assert vm.tracking_label_text == "In Progress"
    assert vm.tracking_chip_cls.startswith("lp-chip")
    assert vm.has_video_preview is True
    assert vm.video_embed_url == "https://www.youtube.com/embed/dQw4w9WgXcQ?rel=0"
    assert vm.thumbnail_url == "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"
    assert vm.thumbnail_fallback_url == "https://img.youtube.com/vi/dQw4w9WgXcQ/hqdefault.jpg"


@pytest.mark.unit
def test_map_course_card_view_for_untracked_course() -> None:
    row = {
        "id": 7,
        "created_by": "alice",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "url": "https://example.com/course",
        "preview_image_url": "https://cdn.example.com/cover.png",
    }
    vm = view_model.map_course_card_view(
        course_row=row,
        tracked_row=None,
        review_summary_row=None,
    )
    assert vm.card_class_suffix == ""
    assert vm.rating_badge == ""
    assert vm.tracking_label_text == "Not tracked"
    assert vm.has_video_preview is False
    assert vm.video_embed_url == ""
    assert vm.thumbnail_url == "https://cdn.example.com/cover.png"
    assert vm.thumbnail_fallback_url == ""


@pytest.mark.unit
def test_map_course_card_view_uses_default_icon_when_non_youtube_has_no_preview() -> None:
    row = {
        "id": 9,
        "created_by": "alice",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "url": "https://fastapi.tiangolo.com/tutorial/testing/",
        "preview_image_url": "",
    }
    vm = view_model.map_course_card_view(
        course_row=row,
        tracked_row=None,
        review_summary_row=None,
    )
    assert vm.has_video_preview is False
    assert vm.thumbnail_url == "https://www.google.com/s2/favicons?domain=fastapi.tiangolo.com&sz=256"
    assert vm.thumbnail_fallback_url == ""


@pytest.mark.unit
def test_map_course_card_view_rejects_low_quality_preview_image() -> None:
    row = {
        "id": 10,
        "created_by": "alice",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "url": "https://fastapi.tiangolo.com/tutorial/testing/",
        "preview_image_url": "https://cdn.example.com/logo-32x32.png",
    }
    vm = view_model.map_course_card_view(
        course_row=row,
        tracked_row=None,
        review_summary_row=None,
    )
    assert vm.thumbnail_url == ""
    assert vm.thumbnail_fallback_url == ""


@pytest.mark.unit
def test_map_course_card_view_keeps_large_logo_style_preview_image() -> None:
    row = {
        "id": 11,
        "created_by": "alice",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
        "url": "https://example.com/course",
        "preview_image_url": "https://cdn.example.com/assets/logo-social-1200x630.png",
    }
    vm = view_model.map_course_card_view(
        course_row=row,
        tracked_row=None,
        review_summary_row=None,
    )
    assert vm.thumbnail_url == "https://cdn.example.com/assets/logo-social-1200x630.png"
