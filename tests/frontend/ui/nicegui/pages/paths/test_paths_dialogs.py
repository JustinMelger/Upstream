from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.paths import dialogs


@pytest.mark.unit
def test_ordered_item_refs_from_detail_prefers_typed_items() -> None:
    detail = {
        "items": [
            {"type": "video", "id": 7},
            {"type": "course", "id": 11},
            {"type": "article", "id": 4},
        ],
        "courses": [{"id": 99}],
    }

    assert dialogs._ordered_item_refs_from_detail(detail) == [
        "video:7",
        "course:11",
        "article:4",
    ]


@pytest.mark.unit
def test_ordered_item_refs_from_detail_falls_back_to_legacy_courses() -> None:
    detail = {"courses": [{"id": 10}, {"id": "12"}, {"id": "bad"}]}

    assert dialogs._ordered_item_refs_from_detail(detail) == ["course:10", "course:12"]


@pytest.mark.unit
def test_append_selected_item_ref_ignores_empty_and_duplicates() -> None:
    calls: list[str] = []
    refs = ["course:10"]

    dialogs._append_selected_item_ref(ordered_item_refs=refs, item_ref="", refresh=lambda: calls.append("refresh"))
    dialogs._append_selected_item_ref(
        ordered_item_refs=refs,
        item_ref="course:10",
        refresh=lambda: calls.append("refresh"),
    )
    dialogs._append_selected_item_ref(
        ordered_item_refs=refs,
        item_ref="video:7",
        refresh=lambda: calls.append("refresh"),
    )

    assert refs == ["course:10", "video:7"]
    assert calls == ["refresh"]
