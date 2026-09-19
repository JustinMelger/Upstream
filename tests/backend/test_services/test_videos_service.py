import pytest

from backend.database.async_repositories.auth import AuthRepository
from backend.database.async_repositories.videos import VideosRepository
from backend.services.auth_service import AuthService
from backend.services.videos_service import VideosService, VideosServiceError


pytestmark = pytest.mark.anyio


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


@pytest.mark.unit
async def test_videos_reads_keep_empty_images_without_http(db_session, monkeypatch):
    """Creation, lists and details never fetch external resource artwork."""
    import httpx

    async def unexpected_http(*args, **kwargs):
        raise AssertionError("Content reads must not fetch URLs")

    monkeypatch.setattr(httpx.AsyncClient, "send", unexpected_http)
    await AuthService(AuthRepository(db_session)).create_user("alice", "test-password-123", "user")
    service = VideosService(VideosRepository(db_session))
    created = await service.create_video(
        payload={"title": "Resource", "description": "Summary", "url": "https://example.com/resource"}, created_by="alice"
    )

    rows = await service.list_videos(query=None, provider=None, category=None)
    detail = await service.get_video_by_id(video_id=int(created["id"]))
    assert rows[0]["preview_image_url"] == ""
    assert detail["preview_image_url"] == ""
