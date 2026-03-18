from __future__ import annotations

from frontend.ui.nicegui.pages.ai_curator.ui_glue import (
    build_path_payload,
    draft_course_to_create_payload,
    normalize_draft_courses,
)


def test_ai_curator_normalize_draft_courses_filters_non_dict_rows() -> None:
    out = normalize_draft_courses([{"title": "X", "provider": "P"}, "bad"])  # type: ignore[list-item]
    assert len(out) == 1
    assert out[0]["title"] == "X"


def test_ai_curator_draft_course_to_payload_maps_fields() -> None:
    out = draft_course_to_create_payload({"title": "A", "duration_hours": 1.5, "url": "https://x"})
    assert out["title"] == "A"
    assert out["duration_hours"] == 1.5
    assert out["url"] == "https://x"


def test_ai_curator_build_path_payload_filters_non_positive_ids() -> None:
    out = build_path_payload(name="N", description="D", course_ids=[1, 0, -1, 2])
    assert out == {
        "name": "N",
        "description": "D",
        "items": [
            {"type": "course", "id": 1, "position": 0},
            {"type": "course", "id": 2, "position": 1},
        ],
    }
