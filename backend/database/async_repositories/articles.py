from __future__ import annotations

from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.async_repositories.datetime_utils import RepositoryDateTimeCodec
from backend.database.models import ArticleRecord
from backend.database.orm_models import Article as ArticleModel


class ArticlesRepository(RepositoryDateTimeCodec):
    """Async SQLAlchemy implementation of article persistence."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository.

        Args:
            session: SQLAlchemy AsyncSession for this request.
        """
        self.session = session

    async def list_articles(self, *, query: str | None, tag: str | None) -> list[ArticleRecord]:
        """List articles with optional filters.

        Args:
            query: Free-text query applied to title/url/tags.
            tag: Optional tag substring filter.

        Returns:
            List of articles ordered by newest first.
        """
        stmt = select(ArticleModel).order_by(ArticleModel.id.desc())

        if query:
            like = f"%{query.lower()}%"
            stmt = stmt.where(
                func.lower(ArticleModel.title).like(like)
                | func.lower(ArticleModel.url).like(like)
                | func.lower(func.coalesce(ArticleModel.tags, "")).like(like)
            )
        if tag:
            tag_like = f"%{tag.lower()}%"
            stmt = stmt.where(func.lower(func.coalesce(ArticleModel.tags, "")).like(tag_like))

        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            ArticleRecord(
                id=int(r.id),
                title=str(r.title or ""),
                url=str(r.url or ""),
                tags=r.tags,
                created_by=str(r.created_by or ""),
                created_at=self._as_iso_or_empty(r.created_at),
            )
            for r in rows
        ]

    async def create_article(
        self, *, title: str, url: str, tags: str | None, created_by: str, created_at: str | datetime
    ) -> int:
        """Create an article.

        Returns:
            Newly created article id.
        """
        row = ArticleModel(title=title, url=url, tags=tags, created_by=created_by, created_at=self._as_datetime(created_at))
        self.session.add(row)
        await self.session.flush()
        return int(row.id)

    async def get_article_by_id(self, article_id: int) -> ArticleRecord | None:
        """Fetch an article by id."""
        result = await self.session.execute(select(ArticleModel).where(ArticleModel.id == article_id).limit(1))
        row = result.scalar_one_or_none()
        if not row:
            return None
        return ArticleRecord(
            id=int(row.id),
            title=str(row.title or ""),
            url=str(row.url or ""),
            tags=row.tags,
            created_by=str(row.created_by or ""),
            created_at=self._as_iso_or_empty(row.created_at),
        )
