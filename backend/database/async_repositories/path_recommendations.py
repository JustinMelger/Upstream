from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.async_repositories.datetime_utils import RepositoryDateTimeCodec
from backend.database.models import PathRecommendationRecord
from backend.database.orm_models import PathRecommendation as PathRecommendationModel


class PathRecommendationsRepository(RepositoryDateTimeCodec):
    """Async SQLAlchemy persistence for path recommendations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_for_path(self, *, path_id: int) -> list[PathRecommendationRecord]:
        """List recommendations for a path (newest first)."""
        result = await self.session.execute(
            select(PathRecommendationModel)
            .where(PathRecommendationModel.path_id == int(path_id))
            .order_by(PathRecommendationModel.id.desc())
        )
        rows = result.scalars().all()
        return [
            PathRecommendationRecord(
                id=int(r.id),
                path_id=int(r.path_id),
                note=r.note,
                created_by=str(r.created_by),
                created_at=self._as_iso(r.created_at),
            )
            for r in rows
        ]

    async def create_recommendation(
        self,
        *,
        path_id: int,
        note: str | None,
        created_by: str,
        created_at: str | datetime,
    ) -> int:
        """Create a recommendation and return id."""
        row = PathRecommendationModel(
            path_id=int(path_id),
            note=note,
            created_by=str(created_by),
            created_at=self._as_datetime(created_at),
        )
        self.session.add(row)
        await self.session.flush()
        return int(row.id)

    async def get_recommendation_for_path_by_user(self, *, path_id: int, created_by: str) -> PathRecommendationRecord | None:
        """Fetch recommendation by (path_id, created_by)."""
        result = await self.session.execute(
            select(PathRecommendationModel)
            .where(PathRecommendationModel.path_id == int(path_id))
            .where(PathRecommendationModel.created_by == str(created_by))
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return PathRecommendationRecord(
            id=int(row.id),
            path_id=int(row.path_id),
            note=row.note,
            created_by=str(row.created_by),
            created_at=self._as_iso(row.created_at),
        )

    async def update_recommendation(self, *, recommendation_id: int, note: str | None, created_at: str | datetime) -> int:
        """Update note/timestamp on an existing recommendation."""
        result = await self.session.execute(
            update(PathRecommendationModel)
            .where(PathRecommendationModel.id == int(recommendation_id))
            .values(note=note, created_at=self._as_datetime(created_at))
        )
        return int(result.rowcount or 0)

    async def delete_recommendation(self, *, recommendation_id: int) -> int:
        """Delete recommendation by id."""
        result = await self.session.execute(
            delete(PathRecommendationModel).where(PathRecommendationModel.id == int(recommendation_id))
        )
        return int(result.rowcount or 0)

    async def recommendation_count_for_paths(self, *, path_ids: list[int]) -> dict[int, int]:
        """Return recommendation counts for each path id."""
        if not path_ids:
            return {}
        result = await self.session.execute(
            select(PathRecommendationModel.path_id, func.count(PathRecommendationModel.id))
            .where(PathRecommendationModel.path_id.in_([int(i) for i in path_ids]))
            .group_by(PathRecommendationModel.path_id)
        )
        out: dict[int, int] = {}
        for path_id, count in result.all():
            try:
                out[int(path_id)] = int(count or 0)
            except (TypeError, ValueError):
                continue
        return out

    async def get_recommendation_by_id(self, recommendation_id: int) -> PathRecommendationRecord | None:
        """Fetch recommendation by id."""
        result = await self.session.execute(
            select(PathRecommendationModel).where(PathRecommendationModel.id == int(recommendation_id)).limit(1)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return PathRecommendationRecord(
            id=int(row.id),
            path_id=int(row.path_id),
            note=row.note,
            created_by=str(row.created_by),
            created_at=self._as_iso(row.created_at),
        )
