from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.async_repositories.datetime_utils import RepositoryDateTimeCodec
from backend.database.models import ArticleReviewRecord
from backend.database.orm_models import ArticleReview as ArticleReviewModel


class ArticleReviewsRepository(RepositoryDateTimeCodec):
    """Async SQLAlchemy implementation of article review persistence."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_article(self, *, article_id: int) -> list[ArticleReviewRecord]:
        """List reviews for an article (newest first)."""
        result = await self.session.execute(
            select(ArticleReviewModel)
            .where(ArticleReviewModel.article_id == int(article_id))
            .order_by(ArticleReviewModel.id.desc())
        )
        rows = result.scalars().all()
        return [
            ArticleReviewRecord(
                id=int(r.id),
                article_id=int(r.article_id),
                rating=int(r.rating),
                text=r.text,
                created_by=str(r.created_by),
                created_at=self._as_iso_or_empty(r.created_at),
            )
            for r in rows
        ]

    async def create_review(
        self,
        *,
        article_id: int,
        rating: int,
        text: str | None,
        created_by: str,
        created_at: str | datetime,
    ) -> int:
        """Create a review and return its id."""
        row = ArticleReviewModel(
            article_id=int(article_id),
            rating=int(rating),
            text=text,
            created_by=str(created_by),
            created_at=self._as_datetime(created_at),
        )
        self.session.add(row)
        await self.session.flush()
        return int(row.id)

    async def get_review_for_article_by_user(self, *, article_id: int, created_by: str) -> ArticleReviewRecord | None:
        """Fetch a review by (article_id, created_by)."""
        result = await self.session.execute(
            select(ArticleReviewModel)
            .where(ArticleReviewModel.article_id == int(article_id))
            .where(ArticleReviewModel.created_by == str(created_by))
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return ArticleReviewRecord(
            id=int(row.id),
            article_id=int(row.article_id),
            rating=int(row.rating),
            text=row.text,
            created_by=str(row.created_by),
            created_at=self._as_iso_or_empty(row.created_at),
        )

    async def update_review(
        self,
        *,
        review_id: int,
        rating: int,
        text: str | None,
        created_at: str | datetime,
    ) -> int:
        """Update a review by id."""
        result = await self.session.execute(
            update(ArticleReviewModel)
            .where(ArticleReviewModel.id == int(review_id))
            .values(rating=int(rating), text=text, created_at=self._as_datetime(created_at))
        )
        return self._rowcount(result)

    async def delete_review(self, *, review_id: int) -> int:
        """Delete a review by id."""
        result = await self.session.execute(delete(ArticleReviewModel).where(ArticleReviewModel.id == int(review_id)))
        return self._rowcount(result)

    async def summaries_for_articles(self, *, article_ids: list[int]) -> dict[int, tuple[float, int]]:
        """Return (avg_rating, count) per article id."""
        if not article_ids:
            return {}
        result = await self.session.execute(
            select(
                ArticleReviewModel.article_id,
                func.avg(ArticleReviewModel.rating),
                func.count(ArticleReviewModel.id),
            )
            .where(ArticleReviewModel.article_id.in_([int(i) for i in article_ids]))
            .group_by(ArticleReviewModel.article_id)
        )
        out: dict[int, tuple[float, int]] = {}
        for article_id, avg_rating, count in result.all():
            try:
                out[int(article_id)] = (float(avg_rating or 0.0), int(count or 0))
            except (TypeError, ValueError):
                continue
        return out

    async def get_review_by_id(self, review_id: int) -> ArticleReviewRecord | None:
        """Fetch a review by id."""
        result = await self.session.execute(select(ArticleReviewModel).where(ArticleReviewModel.id == int(review_id)).limit(1))
        row = result.scalar_one_or_none()
        if not row:
            return None
        return ArticleReviewRecord(
            id=int(row.id),
            article_id=int(row.article_id),
            rating=int(row.rating),
            text=row.text,
            created_by=str(row.created_by),
            created_at=self._as_iso_or_empty(row.created_at),
        )
