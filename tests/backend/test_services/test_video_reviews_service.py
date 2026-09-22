import pytest

from backend.database.async_repositories.auth import AuthRepository
from backend.database.async_repositories.video_reviews import VideoReviewsRepository
from backend.database.async_repositories.videos import VideosRepository
from backend.services.auth_service import AuthService
from backend.services.video_reviews_service import VideoReviewsService, VideoReviewsServiceError
from backend.services.videos_service import VideosService


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_video_review_lifecycle(db_session):
    auth = AuthService(AuthRepository(db_session))
    await auth.create_user("alice", "test-password-123", "user")
    videos = VideosService(VideosRepository(db_session))
    reviews = VideoReviewsService(VideoReviewsRepository(db_session))
    video_id = int(
        (
            await videos.create_video(
                payload={
                    "title": "Video A",
                    "description": "Desc",
                    "provider": "YouTube",
                    "category": "Data",
                    "url": "https://www.youtube.com/watch?v=review-me",
                },
                created_by="alice",
            )
        )["id"]
    )

    created = await reviews.create_review(video_id=video_id, payload={"rating": 4, "text": "Useful"}, created_by="alice")
    assert int(created["video_id"]) == video_id
    assert int(created["rating"]) == 4

    updated = await reviews.create_review(video_id=video_id, payload={"rating": 5, "text": "Updated"}, created_by="alice")
    assert int(updated["id"]) == int(created["id"])
    assert int(updated["rating"]) == 5

    listed = await reviews.list_reviews(video_id=video_id)
    assert len(listed) == 1
    assert int(listed[0]["rating"]) == 5

    assert await reviews.delete_review(review_id=int(created["id"])) is True


@pytest.mark.unit
async def test_video_review_invalid_payload_type_returns_invalid_payload(db_session):
    reviews = VideoReviewsService(VideoReviewsRepository(db_session))
    with pytest.raises(VideoReviewsServiceError) as excinfo:
        await reviews.create_review(video_id=1, payload={"rating": ["bad"], "text": "desc"}, created_by="alice")
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_payload"
