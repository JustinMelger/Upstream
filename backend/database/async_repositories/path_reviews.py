from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.async_repositories.datetime_utils import RepositoryDateTimeCodec
from backend.database.models import PathReviewRecord
from backend.database.orm_models import PathReview as PathReviewModel


class PathReviewsRepository(RepositoryDateTimeCodec):
    """Async SQLAlchemy implementation of path review persistence."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository.

        Args:
            session: SQLAlchemy AsyncSession for this request.
        """
        self.session = session

    async def list_for_path(self, *, path_id: int) -> list[PathReviewRecord]:
        """List reviews for a path (newest first)."""
        result = await self.session.execute(
            select(PathReviewModel).where(PathReviewModel.path_id == path_id).order_by(PathReviewModel.id.desc())
        )
        rows = result.scalars().all()
        return [
            PathReviewRecord(
                id=int(r.id),
                path_id=int(r.path_id),
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
        path_id: int,
        rating: int,
        text: str | None,
        created_by: str,
        created_at: str | datetime,
    ) -> int:
        """Create a review and return its id."""
        row = PathReviewModel(
            path_id=int(path_id),
            rating=int(rating),
            text=text,
            created_by=str(created_by),
            created_at=self._as_datetime(created_at),
        )
        self.session.add(row)
        await self.session.flush()
        return int(row.id)

    async def get_review_for_path_by_user(self, *, path_id: int, created_by: str) -> PathReviewRecord | None:
        """Fetch a review by (path_id, created_by)."""
        result = await self.session.execute(
            select(PathReviewModel)
            .where(PathReviewModel.path_id == int(path_id))
            .where(PathReviewModel.created_by == str(created_by))
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return PathReviewRecord(
            id=int(row.id),
            path_id=int(row.path_id),
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
        """Update a review.

        Returns:
            Number of rows updated.
        """
        result = await self.session.execute(
            update(PathReviewModel)
            .where(PathReviewModel.id == int(review_id))
            .values(rating=int(rating), text=text, created_at=self._as_datetime(created_at))
        )
        return self._rowcount(result)

    async def delete_review(self, *, review_id: int) -> int:
        """Delete a review by id.

        Returns:
            Number of rows deleted.
        """
        result = await self.session.execute(delete(PathReviewModel).where(PathReviewModel.id == int(review_id)))
        return self._rowcount(result)

    async def get_review_by_id(self, review_id: int) -> PathReviewRecord | None:
        """Fetch a review by id."""
        result = await self.session.execute(select(PathReviewModel).where(PathReviewModel.id == review_id).limit(1))
        row = result.scalar_one_or_none()
        if not row:
            return None
        return PathReviewRecord(
            id=int(row.id),
            path_id=int(row.path_id),
            rating=int(row.rating),
            text=row.text,
            created_by=str(row.created_by),
            created_at=self._as_iso_or_empty(row.created_at),
        )
