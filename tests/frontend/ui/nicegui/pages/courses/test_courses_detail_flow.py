from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.courses.detail_flow import open_course_details_flow
from frontend.ui.nicegui.pages.courses.state import CoursesPageState


@pytest.mark.unit
@pytest.mark.anyio
async def test_open_course_details_flow_wires_controller_callbacks(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict = {}

    async def _open_course_details_dialog(**kwargs):  # noqa: ANN003
        captured.update(kwargs)

    from frontend.ui.nicegui.pages.courses import detail_flow as detail_flow_module

    monkeypatch.setattr(detail_flow_module, "open_course_details_dialog", _open_course_details_dialog)

    class _Controller:
        async def load_course_detail_bundle(self, *, course_id: int, cache_scope: str):  # noqa: ANN001
            return {"ok": True}

        async def save_course_review(self, *, course_id: int, rating: int, text: str, cache_scope: str):  # noqa: ANN001
            return {"id": 1, "rating": rating}

        async def delete_course_review(self, *, course_id: int, review_id: int, cache_scope: str):  # noqa: ANN001
            return True

    state = CoursesPageState(review_summary_by_course_id={7: {"course_id": 7, "review_count": 2}})

    await open_course_details_flow(
        course_id=7,
        focus_reviews=True,
        username="alice",
        is_admin=False,
        state=state,
        controller=_Controller(),
        normalize_course_view_mode=lambda focus: "reviews" if focus else "full",
        format_short_date=lambda value: str(value),
    )

    assert int(captured["course_id"]) == 7
    assert captured["focus_reviews"] is True
    assert captured["state"] is state

    bundle = await captured["load_detail_bundle"](7, "alice")
    saved = await captured["save_review"](7, 5, "great", "alice")
    deleted = await captured["delete_review"](7, 3, "alice")
    assert bundle == {"ok": True}
    assert int(saved["rating"]) == 5
    assert deleted is True
