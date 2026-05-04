from __future__ import annotations

from typing import Any

import pytest

from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.domains.videos.controller import VideosPageController


class _Api:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, Any]] = []

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        self.calls.append(("GET", path, params))
        if path == "/videos/7":
            return {"id": 7, "title": "Video 7"}
        if path == "/videos/7/reviews":
            return [{"id": 9, "video_id": 7, "rating": 4, "text": "Good"}]
        return []

    async def post(self, path: str, payload: dict[str, Any]) -> Any:
        self.calls.append(("POST", path, payload))
        return {"id": 9, "video_id": 7, "rating": 5, "text": "Great"}

    async def delete(self, path: str) -> None:
        self.calls.append(("DELETE", path, None))


@pytest.mark.anyio
async def test_videos_controller_review_endpoints() -> None:
    api = _Api()
    controller = VideosPageController(api=api)  # type: ignore[arg-type]

    video = await controller.load_video(video_id=7)
    reviews = await controller.load_video_reviews(video_id=7)
    saved = await controller.save_video_review(video_id=7, rating=5, text="Great")
    deleted = await controller.delete_video_review(video_id=7, review_id=9)

    assert int(video["id"]) == 7
    assert int(reviews[0]["id"]) == 9
    assert int(saved["rating"]) == 5
    assert deleted is True
    assert ("GET", "/videos/7/reviews", None) in api.calls
    assert ("POST", "/videos/7/reviews", {"rating": 5, "text": "Great"}) in api.calls
    assert ("DELETE", "/videos/7/reviews/9", None) in api.calls


@pytest.mark.anyio
async def test_videos_controller_load_list_bundle() -> None:
    class _BundleApi(_Api):
        async def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
            self.calls.append(("GET", path, params))
            if path == "/videos":
                return [{"id": 7, "title": "Video 7"}]
            if path == "/videos/reviews/summary":
                assert params == {"video_ids": [7]}
                return [{"video_id": 7, "avg_rating": 4.5, "review_count": 2}]
            return []

    api = _BundleApi()
    controller = VideosPageController(api=api)  # type: ignore[arg-type]

    bundle = await controller.load_list_bundle()

    assert [int(v["id"]) for v in bundle.videos] == [7]
    assert int((bundle.review_summary_by_video_id[7])["review_count"]) == 2


@pytest.mark.anyio
async def test_videos_controller_load_list_bundle_keeps_videos_when_review_summary_fails() -> None:
    class _BundleApi(_Api):
        async def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
            self.calls.append(("GET", path, params))
            if path == "/videos":
                return [{"id": 7, "title": "Video 7"}]
            if path == "/videos/reviews/summary":
                raise ApiError(status_code=503, message="summary_unavailable")
            return []

    api = _BundleApi()
    controller = VideosPageController(api=api)  # type: ignore[arg-type]

    bundle = await controller.load_list_bundle()

    assert [int(v["id"]) for v in bundle.videos] == [7]
    assert bundle.review_summary_by_video_id == {}
