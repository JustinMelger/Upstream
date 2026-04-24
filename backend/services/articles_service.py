from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from pydantic import ValidationError
from pydantic.dataclasses import dataclass

from backend.core.errors import articles_error_handler, ArticlesServiceError
from backend.database.async_repositories.articles import ArticlesRepository
from backend.database.models import ArticleRecord
from backend.database.tx import session_scope
from backend.services.url_preview_service import UrlPreviewService


@dataclass
class ArticleCreatePayload:
    """Typed service-layer payload for article creation."""

    title: str | None = None
    url: str | None = None
    tags: str | None = None


class ArticlesService:
    """Application service for the Articles domain."""

    def __init__(
        self,
        repo: ArticlesRepository,
        url_preview_service: UrlPreviewService | None = None,
    ):
        """Initialize the service.

        Args:
            repo: Articles repository.
        """
        self._repo = repo
        self._url_preview_service = url_preview_service or UrlPreviewService()

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
        preview_map = await self._resolve_preview_images(rows)
        return [
            self._to_payload(
                r,
                preview_image_url=preview_map.get(int(r.id), ""),
            )
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
            duplicate = await self._repo.find_article_by_url(url=url)
            if duplicate:
                raise ArticlesServiceError(detail="duplicate_url", status_code=409)
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
        preview_map = await self._resolve_preview_images([created])
        return self._to_payload(
            created,
            preview_image_url=preview_map.get(int(created.id), ""),
        )

    @articles_error_handler()
    async def get_article_by_id(self, *, article_id: int) -> dict | None:
        """Fetch one article payload."""
        async with session_scope(self._repo.session):
            article = await self._repo.get_article_by_id(int(article_id))
        if not article:
            return None
        preview_map = await self._resolve_preview_images([article])
        return self._to_payload(article, preview_image_url=preview_map.get(int(article.id), ""))

    @staticmethod
    def _parse_create_payload(payload: dict) -> ArticleCreatePayload:
        """Parse and validate an article create payload."""
        try:
            return ArticleCreatePayload(**dict(payload or {}))
        except ValidationError as exc:
            raise ArticlesServiceError(detail="invalid_payload", status_code=400) from exc

    @staticmethod
    def _to_payload(article: ArticleRecord, *, preview_image_url: str = "") -> dict:
        """Convert an article record to an API payload."""
        return {
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "tags": article.tags,
            "created_by": article.created_by,
            "created_at": article.created_at,
            "preview_image_url": str(preview_image_url or ""),
        }

    async def _resolve_preview_images(self, articles: list[ArticleRecord]) -> dict[int, str]:
        out: dict[int, str] = {}
        if not articles:
            return out
        urls: dict[str, list[int]] = {}
        for row in articles:
            article_id = int(getattr(row, "id", 0) or 0)
            url = str(getattr(row, "url", "") or "").strip()
            if article_id <= 0 or not url:
                continue
            urls.setdefault(url, []).append(article_id)
        if not urls:
            return out

        resolved = await asyncio.gather(
            *(self._url_preview_service.resolve_image_url(source_url=url) for url in urls.keys()),
            return_exceptions=True,
        )
        for url, image_url in zip(urls.keys(), resolved, strict=False):
            image = "" if isinstance(image_url, Exception) else str(image_url or "")
            for article_id in urls.get(url, []):
                out[int(article_id)] = image
        return out
