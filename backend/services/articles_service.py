from __future__ import annotations

from datetime import datetime, timezone

from pydantic import ValidationError
from pydantic.dataclasses import dataclass

from backend.core.errors import articles_error_handler, ArticlesServiceError
from backend.database.async_repositories.articles import ArticlesRepository
from backend.database.tx import session_scope


@dataclass
class ArticleCreatePayload:
    """Typed service-layer payload for article creation."""

    title: str | None = None
    url: str | None = None
    tags: str | None = None


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
        async with session_scope(self._repo.session):
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
        data = self._parse_create_payload(payload)
        title = str(data.title or "").strip()
        url = str(data.url or "").strip()
        tags = str(data.tags or "").strip() or None

        if not title:
            raise ArticlesServiceError(detail="missing_title", status_code=400)
        if not url:
            raise ArticlesServiceError(detail="missing_url", status_code=400)
        if not (url.startswith("http://") or url.startswith("https://")):
            raise ArticlesServiceError(detail="invalid_url", status_code=400)

        created_at = datetime.now(timezone.utc).isoformat()
        async with session_scope(self._repo.session):
            article_id = await self._repo.create_article(
                title=title,
                url=url,
                tags=tags,
                created_by=str(created_by),
                created_at=created_at,
            )

        async with session_scope(self._repo.session):
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

    @staticmethod
    def _parse_create_payload(payload: dict) -> ArticleCreatePayload:
        """Parse and validate an article create payload."""
        try:
            return ArticleCreatePayload(**dict(payload or {}))
        except ValidationError as exc:
            raise ArticlesServiceError(detail="invalid_payload", status_code=400) from exc
