from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.share.helpers import (
    normalize_requested_share_type,
    share_detected_type_text,
    share_route_for_type,
    validate_course_like_publish,
)


@pytest.mark.unit
def test_share_helpers_normalize_video_route_contract() -> None:
    assert normalize_requested_share_type("video") == "video"
    assert normalize_requested_share_type("article") == "article"
    assert normalize_requested_share_type("bad") == "course"
    assert share_route_for_type("video") == "/share/item?type=video"
    assert share_route_for_type("article") == "/share/item?type=article"


@pytest.mark.unit
def test_share_detected_type_text_mentions_mismatched_selection() -> None:
    text = share_detected_type_text(
        current_type="course",
        source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    )
    assert "Detected type: Video." in text
    assert "Current selection: Course." in text


@pytest.mark.unit
def test_validate_course_like_publish_requires_description_and_url() -> None:
    assert (
        validate_course_like_publish(item_type="video", title="Demo", description="", url="https://youtu.be/demo")
        == "Description is required"
    )
    assert (
        validate_course_like_publish(item_type="course", title="Udemy", description="desc", url="")
        == "Valid learning item URL is required"
    )
    assert (
        validate_course_like_publish(item_type="course", title="Udemy", description="desc", url="https://udemy.com/x") is None
    )
