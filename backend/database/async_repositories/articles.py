from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.async_repositories.datetime_utils import RepositoryDateTimeCodec
from backend.database.models import ArticleRecord
from backend.database.orm_models import Article as ArticleModel, PathItem


class ArticlesRepository(RepositoryDateTimeCodec):
    """Async SQLAlchemy implementation of article persistence."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository.

        Args:
            session: SQLAlchemy AsyncSession for this request.
        """
        self.session = session

    async def set_recommendation_note(self, content_id: int, note: str | None) -> None:
        """Persist an explicitly supplied sharing note."""
        await self.session.execute(update(ArticleModel).where(ArticleModel.id == content_id).values(recommendation_note=note))

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
                description=r.description,
                recommendation_note=r.recommendation_note,
                created_by=str(r.created_by or ""),
                created_at=self._as_iso_or_empty(r.created_at),
            )
            for r in rows
        ]

    async def create_article(
        self,
        *,
        title: str,
        url: str,
        tags: str | None,
        created_by: str,
        created_at: str | datetime,
        description: str | None = None,
    ) -> int:
        """Create an article.

        Returns:
            Newly created article id.
        """
        row = ArticleModel(
            title=title,
            description=description,
            url=url,
            tags=tags,
            created_by=created_by,
            created_at=self._as_datetime(created_at),
        )
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
            description=row.description,
            recommendation_note=row.recommendation_note,
            created_by=str(row.created_by or ""),
            created_at=self._as_iso_or_empty(row.created_at),
        )

    async def find_article_by_url(self, *, url: str) -> ArticleRecord | None:
        """Find an article by normalized URL."""
        normalized = str(url or "").strip().lower()
        if not normalized:
            return None
        stmt = (
            select(ArticleModel)
            .where(func.lower(func.trim(ArticleModel.url)) == normalized)
            .order_by(ArticleModel.id.asc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return None
        return ArticleRecord(
            id=int(row.id),
            title=str(row.title or ""),
            url=str(row.url or ""),
            tags=row.tags,
            description=row.description,
            recommendation_note=row.recommendation_note,
            created_by=str(row.created_by or ""),
            created_at=self._as_iso_or_empty(row.created_at),
        )

    async def update_content(self, content_id: int, values: dict) -> None:
        """Apply already validated content fields."""
        await self.session.execute(update(ArticleModel).where(ArticleModel.id == content_id).values(**values))

    async def delete_content(self, content_id: int) -> bool:
        """Delete content and polymorphic path references in the caller transaction."""
        await self.session.execute(delete(PathItem).where(PathItem.item_type == "article", PathItem.item_id == content_id))
        result = await self.session.execute(delete(ArticleModel).where(ArticleModel.id == content_id))
        return self._rowcount(result) > 0
