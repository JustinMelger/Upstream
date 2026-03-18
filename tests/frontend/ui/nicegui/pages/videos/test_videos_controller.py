from __future__ import annotations

import pytest

from frontend.ui.nicegui.pages.videos.controller import VideosPageController


class _FakeApi:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, dict | None]] = []

    async def get(self, path: str, params: dict | None = None):
        self.calls.append(("GET", path, params))
        if path == "/videos/7":
            return {"id": 7, "title": "Video 7"}
        if path == "/videos/7/reviews":
            return [{"id": 9, "video_id": 7, "rating": 4, "text": "Good"}]
        return []

    async def post(self, path: str, payload: dict | None = None):
        self.calls.append(("POST", path, payload))
        return {"id": 9, "video_id": 7, "rating": 5, "text": "Great"}

    async def delete(self, path: str):
        self.calls.append(("DELETE", path, None))
        return {"deleted": True}


@pytest.mark.unit
@pytest.mark.anyio
async def test_videos_controller_review_endpoints() -> None:
    api = _FakeApi()
    controller = VideosPageController(api=api)  # type: ignore[arg-type]

    video = await controller.load_video(video_id=7)
    reviews = await controller.load_video_reviews(video_id=7)
    saved = await controller.save_video_review(video_id=7, rating=5, text="Great")
    deleted = await controller.delete_video_review(video_id=7, review_id=9)

    assert int(video["id"]) == 7
    assert len(reviews) == 1
    assert int(saved["rating"]) == 5
    assert deleted is True
    assert ("GET", "/videos/7/reviews", None) in api.calls
    assert ("POST", "/videos/7/reviews", {"rating": 5, "text": "Great"}) in api.calls
    assert ("DELETE", "/videos/7/reviews/9", None) in api.calls


@pytest.mark.unit
@pytest.mark.anyio
async def test_videos_controller_load_list_bundle() -> None:
    class _BundleApi(_FakeApi):
        async def get(self, path: str, params: dict | None = None):
            self.calls.append(("GET", path, params))
            if path == "/videos":
                return [{"id": 7, "title": "Video 7"}]
            if path == "/videos/reviews/summary":
                assert params == {"video_ids": [7]}
                return [{"video_id": 7, "avg_rating": 4.5, "review_count": 2}]
            return await super().get(path, params=params)

    api = _BundleApi()
    controller = VideosPageController(api=api)  # type: ignore[arg-type]
    bundle = await controller.load_list_bundle()

    assert [int(v["id"]) for v in bundle.videos] == [7]
    assert int((bundle.review_summary_by_video_id[7])["review_count"]) == 2
