from __future__ import annotations

from frontend.ui.nicegui.pages.activity.transitions import begin_activity_load, finalize_activity_load


def test_begin_activity_load_defaults() -> None:
    out = begin_activity_load()
    assert out.loading is True


def test_finalize_activity_load_filters_non_dict_rows() -> None:
    out = finalize_activity_load(rows=[{"message": "ok"}, "bad", {"message": "ok2"}])  # type: ignore[list-item]
    assert out.loading is False
    assert out.events == [{"message": "ok"}, {"message": "ok2"}]
