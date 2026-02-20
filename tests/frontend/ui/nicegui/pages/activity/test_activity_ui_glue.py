from __future__ import annotations

from frontend.ui.nicegui.pages.activity.ui_glue import coerce_target_id, format_when, target_url


def test_activity_target_url_mapping() -> None:
    assert target_url(target_type="course", target_id=7) == "/courses?course_id=7"
    assert target_url(target_type="path", target_id=2) == "/paths?path_id=2"
    assert target_url(target_type="article", target_id=1) == "/articles"
    assert target_url(target_type="unknown", target_id=1) == "/learning"


def test_activity_format_when_accepts_iso_z() -> None:
    out = format_when("2026-02-01T12:30:00Z")
    assert out.startswith("Feb 01, 2026 12:30 UTC")


def test_activity_coerce_target_id() -> None:
    assert coerce_target_id("7") == 7
    assert coerce_target_id(3) == 3
    assert coerce_target_id(0) is None
    assert coerce_target_id("bad") is None
