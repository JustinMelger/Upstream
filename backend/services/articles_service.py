from __future__ import annotations

from datetime import datetime, timezone

from backend.core.errors import articles_error_handler, ArticlesServiceError
from backend.database.async_repositories.articles import ArticlesRepository


class ArticlesService:
    """Application service for the Articles domain."""

    def __init__(self, repo: ArticlesRepository):
        """Initialize the service.

        Args:
            repo: Articles repository.
        """
        self._repo = repo

    @articles_error_handler()
    async def list_articles(self, *, query: str | None, tag: str | None) -> list[dict]:
        """List articles.

        Args:
            query: Optional search query.
            tag: Optional tag substring filter.

        Returns:
            List of article payloads.
        """
        async with self._repo.session.begin():
            rows = await self._repo.list_articles(query=query, tag=tag)
        return [
            {
                "id": r.id,
                "title": r.title,
                "url": r.url,
                "tags": r.tags,
                "created_by": r.created_by,
                "created_at": r.created_at,
            }
            for r in rows
        ]

    @articles_error_handler()
    async def create_article(self, *, payload: dict, created_by: str) -> dict:
        """Create a new article.

        Args:
            payload: Article create payload.
            created_by: Authenticated username.

        Returns:
            Newly created article payload.
        """
        title = str(payload.get("title") or "").strip()
        url = str(payload.get("url") or "").strip()
        tags = str(payload.get("tags") or "").strip() or None

        if not title:
            raise ArticlesServiceError(detail="missing_title", status_code=400)
        if not url:
            raise ArticlesServiceError(detail="missing_url", status_code=400)
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ArticlesServiceError(detail="invalid_url", status_code=400)

        created_at = datetime.now(timezone.utc).isoformat()
        async with self._repo.session.begin():
            article_id = await self._repo.create_article(
                title=title,
                url=url,
                tags=tags,
                created_by=str(created_by),
                created_at=created_at,
            )

        async with self._repo.session.begin():
            created = await self._repo.get_article_by_id(article_id)
        if not created:
            raise ArticlesServiceError(detail="create_failed", status_code=500)
        return {
            "id": created.id,
            "title": created.title,
            "url": created.url,
            "tags": created.tags,
            "created_by": created.created_by,
            "created_at": created.created_at,
        }
