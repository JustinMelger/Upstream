from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.courses.detail_flow import open_course_details_flow
from frontend.ui.nicegui.pages.courses.media import extract_youtube_video_id, render_youtube_embed, youtube_embed_url
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

    deps = captured["deps"]
    bundle = await deps.load_detail_bundle(7, "alice")
    saved = await deps.save_review(7, 5, "great", "alice")
    deleted = await deps.delete_review(7, 3, "alice")
    assert bundle == {"ok": True}
    assert int(saved["rating"]) == 5
    assert deleted is True


@pytest.mark.unit
def test_extract_youtube_video_id_supports_common_youtube_urls() -> None:
    video_id = "dQw4w9WgXcQ"
    assert extract_youtube_video_id(f"https://www.youtube.com/watch?v={video_id}") == video_id
    assert extract_youtube_video_id(f"https://youtu.be/{video_id}") == video_id
    assert extract_youtube_video_id(f"https://www.youtube.com/embed/{video_id}") == video_id
    assert extract_youtube_video_id(f"https://www.youtube.com/shorts/{video_id}") == video_id


@pytest.mark.unit
def test_extract_youtube_video_id_rejects_non_youtube_and_invalid_ids() -> None:
    assert extract_youtube_video_id("https://example.com/watch?v=dQw4w9WgXcQ") is None
    assert extract_youtube_video_id("https://www.youtube.com/watch?v=bad") is None
    assert extract_youtube_video_id("") is None
    assert extract_youtube_video_id(None) is None


@pytest.mark.unit
def test_youtube_embed_url_builder() -> None:
    assert youtube_embed_url("dQw4w9WgXcQ") == "https://www.youtube.com/embed/dQw4w9WgXcQ?rel=0"


@pytest.mark.unit
def test_render_youtube_embed_disables_sanitization() -> None:
    content = render_youtube_embed("https://www.youtube.com/embed/dQw4w9WgXcQ?rel=0")
    assert "iframe" in str(content)
    assert "youtube.com/embed/dQw4w9WgXcQ" in str(content)
