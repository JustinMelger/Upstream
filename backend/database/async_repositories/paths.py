from __future__ import annotations

from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.async_repositories.datetime_utils import RepositoryDateTimeCodec
from backend.database.models import PathLearningItemRecord, PathRecord
from backend.database.orm_models import (
    Article as ArticleModel,
    Course as CourseModel,
    Path as PathModel,
    PathItem as PathItemModel,
    Video as VideoModel,
)


class PathsRepository(RepositoryDateTimeCodec):
    """Async SQLAlchemy implementation of paths persistence."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository.

        Args:
            session: SQLAlchemy AsyncSession for this request.
        """
        self.session = session

    async def set_recommendation_note(self, content_id: int, note: str | None) -> None:
        """Persist an explicitly supplied sharing note."""
        await self.session.execute(update(PathModel).where(PathModel.id == content_id).values(recommendation_note=note))

    async def get_path(self, path_id: int) -> tuple[PathRecord, list[PathLearningItemRecord]] | None:
        """Fetch a path and its ordered learning items.

        Args:
            path_id: Path ID.

        Returns:
            Tuple of (path, ordered learning items) or None.
        """
        result = await self.session.execute(select(PathModel).where(PathModel.id == path_id).limit(1))
        path = result.scalar_one_or_none()
        if not path:
            return None

        items_result = await self.session.execute(
            select(
                PathItemModel.item_type,
                PathItemModel.item_id,
                PathItemModel.position,
            )
            .where(PathItemModel.path_id == path_id)
            .order_by(func.coalesce(PathItemModel.position, 9999).asc(), PathItemModel.id.asc())
        )
        rows: list[Any] = list(items_result.all())
        items = await self._load_learning_items(rows)
        return (
            PathRecord(
                id=path.id,
                name=path.name,
                description=path.description,
                created_by=path.created_by,
                recommendation_note=path.recommendation_note,
            ),
            items,
        )

    async def path_name_exists(self, name: str) -> bool:
        """Check whether a path name exists.

        Args:
            name: Path name.

        Returns:
            True if a path with the name exists.
        """
        result = await self.session.execute(select(PathModel.id).where(func.lower(PathModel.name) == func.lower(name)).limit(1))
        return result.first() is not None

    async def path_name_exists_for_other_id(self, path_id: int, name: str) -> bool:
        """Check whether a path name exists for a different ID.

        Args:
            path_id: Current path ID.
            name: Path name.

        Returns:
            True if another path has the same name.
        """
        result = await self.session.execute(
            select(PathModel.id).where(func.lower(PathModel.name) == func.lower(name)).where(PathModel.id != path_id).limit(1)
        )
        return result.first() is not None

    async def create_path_with_items(
        self, name: str, description: str | None, items: list[dict[str, int | str]], created_by: str | None
    ) -> int:
        """Create a path and its ordered learning-item links.

        Args:
            name: Path name.
            description: Optional description.
            items: Ordered list of typed learning-item references.

        Returns:
            New path ID.
        """
        path = PathModel(name=name, description=description, created_by=created_by)
        self.session.add(path)
        await self.session.flush()

        if items:
            self.session.add_all(
                [
                    PathItemModel(
                        path_id=path.id,
                        item_type=str(item.get("type") or ""),
                        item_id=int(item.get("id") or 0),
                        position=idx,
                    )
                    for idx, item in enumerate(items)
                ]
            )
        return int(path.id)

    async def update_path_with_items(
        self, path_id: int, name: str, description: str | None, items: list[dict[str, int | str]]
    ) -> int:
        """Update a path and replace its learning-item ordering.

        Args:
            path_id: Path ID.
            name: Path name.
            description: Optional description.
            items: Ordered list of typed learning-item references.

        Returns:
            Number of rows updated in the paths table.
        """
        result = await self.session.execute(
            update(PathModel).where(PathModel.id == path_id).values(name=name, description=description)
        )
        await self.session.execute(delete(PathItemModel).where(PathItemModel.path_id == path_id))
        if items:
            self.session.add_all(
                [
                    PathItemModel(
                        path_id=path_id,
                        item_type=str(item.get("type") or ""),
                        item_id=int(item.get("id") or 0),
                        position=idx,
                    )
                    for idx, item in enumerate(items)
                ]
            )
        return self._rowcount(result)

    async def delete_path_with_items(self, path_id: int) -> int:
        """Delete a path and its typed learning-item links.

        Args:
            path_id: Path ID.

        Returns:
            Number of paths deleted.
        """
        await self.session.execute(delete(PathItemModel).where(PathItemModel.path_id == path_id))
        result = await self.session.execute(delete(PathModel).where(PathModel.id == path_id))
        return self._rowcount(result)

    async def has_missing_learning_items(self, items: list[dict[str, int | str]]) -> bool:
        """Return whether any typed path-item reference does not exist."""
        grouped: dict[str, set[int]] = {"course": set(), "video": set(), "article": set()}
        for item in list(items or []):
            item_type = str(item.get("type") or "").strip().lower()
            item_id = int(item.get("id") or 0)
            if item_type not in grouped or item_id <= 0:
                return True
            grouped[item_type].add(item_id)

        if grouped["course"]:
            result = await self.session.execute(select(CourseModel.id).where(CourseModel.id.in_(grouped["course"])))
            if {int(row[0]) for row in result.all()} != grouped["course"]:
                return True
        if grouped["video"]:
            result = await self.session.execute(select(VideoModel.id).where(VideoModel.id.in_(grouped["video"])))
            if {int(row[0]) for row in result.all()} != grouped["video"]:
                return True
        if grouped["article"]:
            result = await self.session.execute(select(ArticleModel.id).where(ArticleModel.id.in_(grouped["article"])))
            if {int(row[0]) for row in result.all()} != grouped["article"]:
                return True
        return False

    async def _load_learning_items(self, rows: list[Any]) -> list[PathLearningItemRecord]:
        """Resolve typed path-item rows into ordered learning-item records."""
        grouped_ids: dict[str, set[int]] = {"course": set(), "video": set(), "article": set()}
        normalized_rows: list[tuple[str, int, int | None]] = []
        for row in rows:
            item_type = str(self._row_value(row, "item_type") or "").strip().lower()
            item_id = int(self._row_value(row, "item_id") or 0)
            raw_position = self._row_value(row, "position")
            position = int(raw_position) if raw_position is not None else None
            normalized_rows.append((item_type, item_id, position))
            if item_type in grouped_ids and item_id > 0:
                grouped_ids[item_type].add(item_id)

        course_map = await self._load_course_items(grouped_ids["course"])
        video_map = await self._load_video_items(grouped_ids["video"])
        article_map = await self._load_article_items(grouped_ids["article"])

        out: list[PathLearningItemRecord] = []
        for item_type, item_id, position in normalized_rows:
            if item_type == "course" and item_id in course_map:
                payload = course_map[item_id]
            elif item_type == "video" and item_id in video_map:
                payload = video_map[item_id]
            elif item_type == "article" and item_id in article_map:
                payload = article_map[item_id]
            else:
                continue
            raw_duration = payload.get("duration_hours")
            out.append(
                PathLearningItemRecord(
                    item_type=item_type,
                    id=item_id,
                    title=str(payload.get("title") or ""),
                    description=str(payload.get("description") or "") or None,
                    provider=str(payload.get("provider") or "") or None,
                    category=str(payload.get("category") or "") or None,
                    level=str(payload.get("level") or "") or None,
                    duration_hours=float(str(raw_duration)) if raw_duration is not None else None,
                    url=str(payload.get("url") or "") or None,
                    preview_image_url=str(payload.get("preview_image_url") or "") or None,
                    position=position,
                )
            )
        return out

    @staticmethod
    def _row_value(row: Any, key: str) -> Any:
        """Read a field from SQLAlchemy rows."""
        if hasattr(row, key):
            return getattr(row, key)
        return None

    async def _load_course_items(self, ids: set[int]) -> dict[int, dict[str, object]]:
        """Load course-backed path items."""
        if not ids:
            return {}
        result = await self.session.execute(
            select(
                CourseModel.id,
                CourseModel.title,
                CourseModel.description,
                CourseModel.provider,
                CourseModel.category,
                CourseModel.level,
                CourseModel.duration_hours,
                CourseModel.url,
            ).where(CourseModel.id.in_(ids))
        )
        return {
            int(row.id): {
                "title": row.title,
                "description": row.description,
                "provider": row.provider,
                "category": row.category,
                "level": row.level,
                "duration_hours": row.duration_hours,
                "url": row.url,
                "preview_image_url": "",
            }
            for row in result.all()
        }

    async def _load_video_items(self, ids: set[int]) -> dict[int, dict[str, object]]:
        """Load video-backed path items."""
        if not ids:
            return {}
        result = await self.session.execute(
            select(
                VideoModel.id,
                VideoModel.title,
                VideoModel.description,
                VideoModel.provider,
                VideoModel.category,
                VideoModel.url,
            ).where(VideoModel.id.in_(ids))
        )
        return {
            int(row.id): {
                "title": row.title,
                "description": row.description,
                "provider": row.provider,
                "category": row.category,
                "level": "",
                "duration_hours": None,
                "url": row.url,
                "preview_image_url": "",
            }
            for row in result.all()
        }

    async def _load_article_items(self, ids: set[int]) -> dict[int, dict[str, object]]:
        """Load article-backed path items."""
        if not ids:
            return {}
        result = await self.session.execute(
            select(
                ArticleModel.id,
                ArticleModel.title,
                ArticleModel.description,
                ArticleModel.url,
            ).where(ArticleModel.id.in_(ids))
        )
        return {
            int(row.id): {
                "title": row.title,
                "description": row.description or "",
                "provider": "",
                "category": "",
                "level": "",
                "duration_hours": None,
                "url": row.url,
                "preview_image_url": "",
            }
            for row in result.all()
        }
