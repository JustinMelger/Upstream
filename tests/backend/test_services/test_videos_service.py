import pytest

from backend.database.async_repositories.auth import AuthRepository
from backend.database.async_repositories.videos import VideosRepository
from backend.services.auth_service import AuthService
from backend.services.videos_service import VideosService, VideosServiceError


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_list_videos_includes_preview_image_url_from_preview_service(db_session):
    class _PreviewService:
        async def resolve_image_url(self, *, source_url: str) -> str:
            if "youtube.com" in source_url:
                return "https://cdn.example.com/video-og.png"
            return ""

    auth = AuthService(AuthRepository(db_session))
    await auth.create_user("alice", "pass123", "user")
    service = VideosService(VideosRepository(db_session), url_preview_service=_PreviewService())
    await service.create_video(
        payload={
            "title": "Video",
            "description": "desc",
            "provider": "YouTube",
            "category": "Programming",
            "url": "https://www.youtube.com/watch?v=abc123",
        },
        created_by="alice",
    )

    rows = await service.list_videos(query=None, provider=None, category=None)
    assert rows[0]["preview_image_url"] == "https://cdn.example.com/video-og.png"


@pytest.mark.unit
async def test_create_video_invalid_payload_type_returns_invalid_payload(db_session):
    service = VideosService(VideosRepository(db_session))
    with pytest.raises(VideosServiceError) as excinfo:
        await service.create_video(
            payload={"title": ["bad"], "description": "desc", "url": "https://example.com/video"},
            created_by="admin",
        )
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_payload"
