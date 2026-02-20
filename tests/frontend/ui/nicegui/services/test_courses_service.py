from __future__ import annotations

import pytest

from frontend.ui.nicegui.services import courses_service


class _FakeApi:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict | None]] = []

    async def get(self, path: str, params: dict | None = None):
        self.calls.append(("GET", path, params))
        if path == "/courses":
            return [{"id": 1, "title": "C1"}]
        if path == "/tracking":
            return [{"course_id": "1", "status": "in_progress"}, {"course_id": "bad", "status": "completed"}]
        if path == "/courses/reviews/summary":
            return [
                {"course_id": 1, "review_count": 2},
                {"course_id": "2", "review_count": 1},
                {"course_id": "bad", "review_count": 9},
            ]
        if path == "/courses/recommendations/summary":
            return [
                {"course_id": 1, "recommendation_count": 3},
                {"course_id": "2", "recommendation_count": 1},
                {"course_id": "bad", "recommendation_count": 9},
            ]
        return []


class _FakeDetailApi:
    def __init__(self) -> None:
        self.calls: list[str] = []

    async def get(self, path: str, params: dict | None = None):
        del params
        self.calls.append(path)
        if path.endswith("/reviews"):
            return [{"id": 1, "rating": 5}]
        if path.endswith("/recommendations"):
            return [{"id": 1, "created_by": "alice"}]
        return {"id": 7, "title": "FastAPI"}


@pytest.mark.unit
def test_index_tracking_by_course_id_ignores_invalid_ids() -> None:
    out = courses_service.index_tracking_by_course_id(
        [{"course_id": "1", "status": "x"}, {"course_id": "bad"}, {"course_id": None}, "bad"]
    )
    assert out == {1: {"course_id": "1", "status": "x"}}


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_courses_and_tracking_passes_params_and_indexes_tracking() -> None:
    api = _FakeApi()
    courses, tracking = await courses_service.load_courses_and_tracking(
        api=api,
        course_params={"q": "fastapi", "provider": "Docs"},
    )
    assert [int(c["id"]) for c in courses] == [1]
    assert tracking == {1: {"course_id": "1", "status": "in_progress"}}
    assert ("GET", "/courses", {"q": "fastapi", "provider": "Docs"}) in api.calls
    assert ("GET", "/tracking", None) in api.calls


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_review_and_recommendation_summaries_filter_invalid_rows() -> None:
    api = _FakeApi()
    reviews = await courses_service.load_review_summaries(api=api, course_ids=[1, 2, 0, -1])
    recs = await courses_service.load_recommendation_summaries(api=api, course_ids=[1, 2, 0, -1])
    assert set(reviews.keys()) == {1, 2}
    assert set(recs.keys()) == {1, 2}
    assert reviews[1]["review_count"] == 2
    assert recs[1]["recommendation_count"] == 3


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_summary_helpers_short_circuit_on_empty_ids() -> None:
    api = _FakeApi()
    reviews = await courses_service.load_review_summaries(api=api, course_ids=[])
    recs = await courses_service.load_recommendation_summaries(api=api, course_ids=[])
    assert reviews == {}
    assert recs == {}
    assert all(call[1] != "/courses/reviews/summary" for call in api.calls)
    assert all(call[1] != "/courses/recommendations/summary" for call in api.calls)


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_course_detail_bundle_uses_ttl_cache_and_expires() -> None:
    courses_service.clear_course_detail_cache()
    api = _FakeDetailApi()
    now = {"t": 100.0}

    def _now() -> float:
        return float(now["t"])

    first = await courses_service.load_course_detail_bundle(api=api, course_id=7, now_fn=_now, ttl_seconds=20.0)
    second = await courses_service.load_course_detail_bundle(api=api, course_id=7, now_fn=_now, ttl_seconds=20.0)
    assert first.course["title"] == "FastAPI"
    assert second.course["title"] == "FastAPI"
    assert api.calls.count("/courses/7") == 1
    assert api.calls.count("/courses/7/reviews") == 1
    assert api.calls.count("/courses/7/recommendations") == 1

    now["t"] = 121.0
    await courses_service.load_course_detail_bundle(api=api, course_id=7, now_fn=_now, ttl_seconds=20.0)
    assert api.calls.count("/courses/7") == 2


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_course_detail_bundle_cache_can_be_invalidated() -> None:
    courses_service.clear_course_detail_cache()
    api = _FakeDetailApi()
    await courses_service.load_course_detail_bundle(api=api, course_id=7)
    await courses_service.load_course_detail_bundle(api=api, course_id=7)
    assert api.calls.count("/courses/7") == 1
    courses_service.clear_course_detail_cache(course_id=7)
    await courses_service.load_course_detail_bundle(api=api, course_id=7)
    assert api.calls.count("/courses/7") == 2
