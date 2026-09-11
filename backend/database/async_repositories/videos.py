from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.async_repositories.datetime_utils import RepositoryDateTimeCodec
from backend.database.models import VideoRecord
from backend.database.orm_models import PathItem, Video as VideoModel


class VideosRepository(RepositoryDateTimeCodec):
    """Async SQLAlchemy implementation of video persistence."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository."""
        self.session = session

    async def set_recommendation_note(self, content_id: int, note: str | None) -> None:
        """Persist an explicitly supplied sharing note."""
        await self.session.execute(update(VideoModel).where(VideoModel.id == content_id).values(recommendation_note=note))

    async def list_videos(self, *, query: str | None, provider: str | None, category: str | None) -> list[VideoRecord]:
        """List videos with optional filters."""
        stmt = select(VideoModel).order_by(VideoModel.id.desc())
        if query:
            like = f"%{query.lower()}%"
            stmt = stmt.where(
                func.lower(VideoModel.title).like(like)
                | func.lower(func.coalesce(VideoModel.description, "")).like(like)
                | func.lower(func.coalesce(VideoModel.provider, "")).like(like)
                | func.lower(func.coalesce(VideoModel.category, "")).like(like)
                | func.lower(VideoModel.url).like(like)
            )
        if provider:
            stmt = stmt.where(VideoModel.provider == provider)
        if category:
            stmt = stmt.where(VideoModel.category == category)
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        return [
            VideoRecord(
                id=int(row.id),
                title=str(row.title or ""),
                description=str(row.description or ""),
                provider=row.provider,
                category=row.category,
                url=str(row.url or ""),
                recommendation_note=row.recommendation_note,
                created_by=str(row.created_by or ""),
                created_at=self._as_iso_or_empty(row.created_at),
            )
            for row in rows
        ]

    async def get_video_by_id(self, video_id: int) -> VideoRecord | None:
        """Fetch a video by id."""
        result = await self.session.execute(select(VideoModel).where(VideoModel.id == int(video_id)).limit(1))
        row = result.scalar_one_or_none()
        if not row:
            return None
        return VideoRecord(
            id=int(row.id),
            title=str(row.title or ""),
            description=str(row.description or ""),
            provider=row.provider,
            category=row.category,
            url=str(row.url or ""),
            recommendation_note=row.recommendation_note,
            created_by=str(row.created_by or ""),
            created_at=self._as_iso_or_empty(row.created_at),
        )

    async def create_video(
        self,
        *,
        title: str,
        description: str,
        provider: str | None,
        category: str | None,
        url: str,
        created_by: str,
        created_at: str | datetime,
    ) -> int:
        """Create a video row and return its id."""
        row = VideoModel(
            title=title,
            description=description,
            provider=provider,
            category=category,
            url=url,
            created_by=created_by,
            created_at=self._as_datetime(created_at),
        )
        self.session.add(row)
        await self.session.flush()
        return int(row.id)

    async def find_video_by_url(self, *, url: str) -> VideoRecord | None:
        """Find a video by normalized URL."""
        normalized = str(url or "").strip().lower()
        if not normalized:
            return None
        stmt = (
            select(VideoModel).where(func.lower(func.trim(VideoModel.url)) == normalized).order_by(VideoModel.id.asc()).limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return None
        return VideoRecord(
            id=int(row.id),
            title=str(row.title or ""),
            description=str(row.description or ""),
            provider=row.provider,
            category=row.category,
            url=str(row.url or ""),
            recommendation_note=row.recommendation_note,
            created_by=str(row.created_by or ""),
            created_at=self._as_iso_or_empty(row.created_at),
        )

    async def update_content(self, content_id: int, values: dict) -> None:
        """Apply already validated content fields."""
        await self.session.execute(update(VideoModel).where(VideoModel.id == content_id).values(**values))

    async def delete_content(self, content_id: int) -> bool:
        """Delete content and polymorphic path references in the caller transaction."""
        await self.session.execute(delete(PathItem).where(PathItem.item_type == "video", PathItem.item_id == content_id))
        result = await self.session.execute(delete(VideoModel).where(VideoModel.id == content_id))
        return self._rowcount(result) > 0
