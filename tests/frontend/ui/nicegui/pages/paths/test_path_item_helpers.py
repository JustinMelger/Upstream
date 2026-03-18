from __future__ import annotations

from frontend.ui.nicegui.pages.paths.item_helpers import (
    build_path_item_payloads,
    count_course_items,
    decode_path_item_ref,
    encode_path_item_ref,
    path_course_ids,
)


def test_encode_and_decode_path_item_ref_round_trip() -> None:
    raw = encode_path_item_ref(item_type="video", item_id=12)
    assert raw == "video:12"
    assert decode_path_item_ref(raw) == ("video", 12)


def test_build_path_item_payloads_preserves_order() -> None:
    out = build_path_item_payloads(["video:7", "course:5", "article:3"])
    assert out == [
        {"type": "video", "id": 7, "position": 0},
        {"type": "course", "id": 5, "position": 1},
        {"type": "article", "id": 3, "position": 2},
    ]


def test_path_course_ids_prefers_typed_items_when_present() -> None:
    detail = {
        "items": [
            {"type": "video", "id": 7},
            {"type": "course", "id": 5},
            {"type": "article", "id": 3},
            {"type": "course", "id": 9},
        ],
        "courses": [{"id": 1}],
    }
    assert path_course_ids(detail=detail) == [5, 9]
    assert count_course_items(detail=detail) == 2


def test_path_course_ids_falls_back_to_legacy_courses() -> None:
    detail = {"courses": [{"id": 11}, {"id": "12"}]}
    assert path_course_ids(detail=detail) == [11, 12]
    assert count_course_items(detail=detail) == 2
