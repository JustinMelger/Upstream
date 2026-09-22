from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.async_repositories.datetime_utils import RepositoryDateTimeCodec
from backend.database.models import VideoReviewRecord
from backend.database.orm_models import VideoReview as VideoReviewModel


class VideoReviewsRepository(RepositoryDateTimeCodec):
    """Async SQLAlchemy implementation of video review persistence."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository.

        Args:
            session: Active async SQLAlchemy session.

        """
        self.session = session

    async def list_for_video(self, *, video_id: int) -> list[VideoReviewRecord]:
        """List reviews for a video (newest first)."""
        result = await self.session.execute(
            select(VideoReviewModel).where(VideoReviewModel.video_id == int(video_id)).order_by(VideoReviewModel.id.desc())
        )
        rows = result.scalars().all()
        return [
            VideoReviewRecord(
                id=int(r.id),
                video_id=int(r.video_id),
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
        video_id: int,
        rating: int,
        text: str | None,
        created_by: str,
        created_at: str | datetime,
    ) -> int:
        """Create a review and return its id."""
        row = VideoReviewModel(
            video_id=int(video_id),
            rating=int(rating),
            text=text,
            created_by=str(created_by),
            created_at=self._as_datetime(created_at),
        )
        self.session.add(row)
        await self.session.flush()
        return int(row.id)

    async def get_review_for_video_by_user(self, *, video_id: int, created_by: str) -> VideoReviewRecord | None:
        """Fetch a review by (video_id, created_by)."""
        result = await self.session.execute(
            select(VideoReviewModel)
            .where(VideoReviewModel.video_id == int(video_id))
            .where(VideoReviewModel.created_by == str(created_by))
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return VideoReviewRecord(
            id=int(row.id),
            video_id=int(row.video_id),
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
            update(VideoReviewModel)
            .where(VideoReviewModel.id == int(review_id))
            .values(rating=int(rating), text=text, created_at=self._as_datetime(created_at))
        )
        return self._rowcount(result)

    async def delete_review(self, *, review_id: int) -> int:
        """Delete a review by id."""
        result = await self.session.execute(delete(VideoReviewModel).where(VideoReviewModel.id == int(review_id)))
        return self._rowcount(result)

    async def get_review_by_id(self, review_id: int) -> VideoReviewRecord | None:
        """Fetch a review by id."""
        result = await self.session.execute(select(VideoReviewModel).where(VideoReviewModel.id == int(review_id)).limit(1))
        row = result.scalar_one_or_none()
        if not row:
            return None
        return VideoReviewRecord(
            id=int(row.id),
            video_id=int(row.video_id),
            rating=int(row.rating),
            text=row.text,
            created_by=str(row.created_by),
            created_at=self._as_iso_or_empty(row.created_at),
        )
