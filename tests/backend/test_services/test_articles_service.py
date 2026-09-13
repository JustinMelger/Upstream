import pytest

from backend.database.async_repositories.articles import ArticlesRepository
from backend.database.async_repositories.auth import AuthRepository
from backend.services.articles_service import ArticlesService
from backend.services.auth_service import AuthService


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_articles_reads_keep_empty_images_without_http(db_session, monkeypatch):
    """Creation, lists and details never fetch external resource artwork."""
    import httpx

    async def unexpected_http(*args, **kwargs):
        raise AssertionError("Content reads must not fetch URLs")

    monkeypatch.setattr(httpx.AsyncClient, "send", unexpected_http)
    await AuthService(AuthRepository(db_session)).create_user("alice", "pass123", "user")
    service = ArticlesService(ArticlesRepository(db_session))
    created = await service.create_article(
        payload={"title": "Resource", "description": "Summary", "url": "https://example.com/resource"}, created_by="alice"
    )

    rows = await service.list_articles(query=None, tag=None)
    detail = await service.get_article_by_id(article_id=int(created["id"]))
    assert rows[0]["preview_image_url"] == ""
    assert detail["preview_image_url"] == ""
