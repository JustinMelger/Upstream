import pytest

from backend.database.async_repositories.auth import AuthRepository
from backend.database.async_repositories.articles import ArticlesRepository
from backend.services.auth_service import AuthService
from backend.services.articles_service import ArticlesService


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_list_articles_includes_preview_image_url_from_preview_service(db_session):
    """List payload includes resolved preview image URLs."""

    class _PreviewService:
        async def resolve_image_url(self, *, source_url: str) -> str:
            if "docs.example.com" in source_url:
                return "https://cdn.example.com/docs-og.png"
            return ""

    auth = AuthService(AuthRepository(db_session))
    await auth.create_user("alice", "pass123", "user")
    service = ArticlesService(ArticlesRepository(db_session), url_preview_service=_PreviewService())
    await service.create_article(
        payload={"title": "Docs", "url": "https://docs.example.com/page", "tags": "docs"},
        created_by="alice",
    )
    await service.create_article(
        payload={"title": "No image", "url": "https://example.net/page", "tags": "misc"},
        created_by="alice",
    )

    rows = await service.list_articles(query=None, tag=None)
    by_title = {str(r.get("title")): r for r in rows}
    assert by_title["Docs"]["preview_image_url"] == "https://cdn.example.com/docs-og.png"
    assert by_title["No image"]["preview_image_url"] == ""


@pytest.mark.unit
async def test_list_articles_preview_resolver_deduplicates_shared_urls(db_session):
    """Preview resolver is called once per unique URL and shared across matching rows."""
    calls: list[str] = []

    class _PreviewService:
        async def resolve_image_url(self, *, source_url: str) -> str:
            calls.append(str(source_url))
            return "https://cdn.example.com/shared.png"

    auth = AuthService(AuthRepository(db_session))
    await auth.create_user("alice", "pass123", "user")
    service = ArticlesService(ArticlesRepository(db_session), url_preview_service=_PreviewService())
    shared_url = "https://example.com/shared"
    await service.create_article(payload={"title": "A", "url": shared_url}, created_by="alice")
    await service.create_article(payload={"title": "B", "url": shared_url}, created_by="alice")
    calls.clear()

    rows = await service.list_articles(query=None, tag=None)
    assert len(rows) == 2
    assert calls == [shared_url]
    assert all(str(r.get("preview_image_url") or "") == "https://cdn.example.com/shared.png" for r in rows)
