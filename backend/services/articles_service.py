from __future__ import annotations

from datetime import datetime, timezone

from pydantic import ValidationError
from pydantic.dataclasses import dataclass

from backend.core.errors import articles_error_handler, ArticlesServiceError
from backend.database.async_repositories.articles import ArticlesRepository
from backend.database.models import ArticleRecord
from backend.database.tx import session_scope
from backend.services.content_edit import normalize_article_description, validate_content_edit
from backend.services.recommendation_notes import normalize_note


@dataclass
class ArticleCreatePayload:
    """Typed service-layer payload for article creation."""

    description: str | None = None
    recommendation_note: str | None = None
    title: str | None = None
    url: str | None = None
    tags: str | None = None


class ArticlesService:
    """Application service for the Articles domain."""

    def __init__(
        self,
        repo: ArticlesRepository,
    ):
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
        return [self._to_payload(r) for r in rows]

    @articles_error_handler()
    async def create_article(self, *, payload: dict, created_by: str) -> dict:
        """Create a new article.

        Args:
            payload: Article create payload.
            created_by: Authenticated username.

        Returns:
            Newly created article payload.
        """
        note = normalize_note(payload.get("recommendation_note"))
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
            duplicate = await self._repo.find_article_by_url(url=url)
            if duplicate:
                raise ArticlesServiceError(detail="duplicate_url", status_code=409)
            article_id = await self._repo.create_article(
                title=title,
                description=normalize_article_description(data.description),
                url=url,
                tags=tags,
                created_by=str(created_by),
                created_at=created_at,
            )

            await self._repo.set_recommendation_note(article_id, note)

        async with session_scope(self._repo.session):
            created = await self._repo.get_article_by_id(article_id)
        if not created:
            raise ArticlesServiceError(detail="create_failed", status_code=500)
        return self._to_payload(created)

    @articles_error_handler()
    async def get_article_by_id(self, *, article_id: int) -> dict | None:
        """Fetch one article payload."""
        async with session_scope(self._repo.session):
            article = await self._repo.get_article_by_id(int(article_id))
        if not article:
            return None
        return self._to_payload(article)

    async def update_article(self, content_id: int, payload: dict) -> dict | None:
        """Validate an edit and preserve omitted fields."""
        async with session_scope(self._repo.session):
            existing = await self._repo.get_article_by_id(content_id)
            if not existing:
                return None
            values = validate_content_edit(payload, kind="article")
            if "url" in values:
                duplicate = await self._repo.find_article_by_url(url=values["url"])
                if duplicate and duplicate.id != content_id:
                    raise ArticlesServiceError(detail="duplicate_url", status_code=409)
            await self._repo.update_content(content_id, values)
        return await self.get_article_by_id(article_id=content_id)

    async def delete_article(self, content_id: int) -> bool:
        """Remove content, reviews and path references transactionally."""
        async with session_scope(self._repo.session):
            return await self._repo.delete_content(content_id)

    @staticmethod
    def _parse_create_payload(payload: dict) -> ArticleCreatePayload:
        """Parse and validate an article create payload."""
        try:
            return ArticleCreatePayload(**dict(payload or {}))
        except ValidationError as exc:
            raise ArticlesServiceError(detail="invalid_payload", status_code=400) from exc

    @staticmethod
    def _to_payload(article: ArticleRecord) -> dict:
        """Convert an article record to an API payload."""
        return {
            "id": article.id,
            "title": article.title,
            "description": article.description,
            "url": article.url,
            "tags": article.tags,
            "created_by": article.created_by,
            "recommendation_note": article.recommendation_note,
            "created_at": article.created_at,
            "preview_image_url": "",
        }
