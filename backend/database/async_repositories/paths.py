from __future__ import annotations

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import PathCourseRecord, PathRecord
from backend.database.orm_models import Course as CourseModel, Path as PathModel, PathCourse as PathCourseModel


class PathsRepository:
    """Async SQLAlchemy implementation of paths persistence."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository.

        Args:
            session: SQLAlchemy AsyncSession for this request.
        """
        self.session = session

    async def list_paths(self) -> list[PathRecord]:
        """List paths.

        Returns:
            List of path records.
        """
        result = await self.session.execute(select(PathModel).order_by(PathModel.name.asc()))
        rows = result.scalars().all()
        return [PathRecord(id=row.id, name=row.name, description=row.description, created_by=row.created_by) for row in rows]

    async def get_path(self, path_id: int) -> tuple[PathRecord, list[PathCourseRecord]] | None:
        """Fetch a path and its course list.

        Args:
            path_id: Path ID.

        Returns:
            Tuple of (path, ordered courses) or None.
        """
        result = await self.session.execute(select(PathModel).where(PathModel.id == path_id).limit(1))
        path = result.scalar_one_or_none()
        if not path:
            return None

        courses_result = await self.session.execute(
            select(
                CourseModel.id,
                CourseModel.title,
                CourseModel.provider,
                CourseModel.category,
                CourseModel.level,
                CourseModel.duration_hours,
                CourseModel.url,
                PathCourseModel.position,
            )
            .join(PathCourseModel, CourseModel.id == PathCourseModel.course_id)
            .where(PathCourseModel.path_id == path_id)
            .order_by(func.coalesce(PathCourseModel.position, 9999).asc(), CourseModel.title.asc())
        )
        courses = courses_result.all()
        return (
            PathRecord(id=path.id, name=path.name, description=path.description, created_by=path.created_by),
            [
                PathCourseRecord(
                    id=row.id,
                    title=row.title or "",
                    provider=row.provider,
                    category=row.category,
                    level=row.level,
                    duration_hours=row.duration_hours,
                    url=row.url,
                    position=row.position,
                )
                for row in courses
            ],
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

    async def create_path_with_courses(
        self, name: str, description: str | None, course_ids: list[int], created_by: str | None
    ) -> int:
        """Create a path and its ordered course links.

        Args:
            name: Path name.
            description: Optional description.
            course_ids: Ordered list of course IDs.

        Returns:
            New path ID.
        """
        path = PathModel(name=name, description=description, created_by=created_by)
        self.session.add(path)
        await self.session.flush()

        if course_ids:
            self.session.add_all(
                [
                    PathCourseModel(path_id=path.id, course_id=int(course_id), position=idx)
                    for idx, course_id in enumerate(course_ids)
                ]
            )
        return int(path.id)

    async def update_path_with_courses(self, path_id: int, name: str, description: str | None, course_ids: list[int]) -> int:
        """Update a path and replace its course ordering.

        Args:
            path_id: Path ID.
            name: Path name.
            description: Optional description.
            course_ids: Ordered list of course IDs.

        Returns:
            Number of rows updated in the paths table.
        """
        result = await self.session.execute(
            update(PathModel).where(PathModel.id == path_id).values(name=name, description=description)
        )
        await self.session.execute(delete(PathCourseModel).where(PathCourseModel.path_id == path_id))
        if course_ids:
            self.session.add_all(
                [
                    PathCourseModel(path_id=path_id, course_id=int(course_id), position=idx)
                    for idx, course_id in enumerate(course_ids)
                ]
            )
        return int(result.rowcount or 0)

    async def delete_path_with_courses(self, path_id: int) -> int:
        """Delete a path and its course links.

        Args:
            path_id: Path ID.

        Returns:
            Number of paths deleted.
        """
        await self.session.execute(delete(PathCourseModel).where(PathCourseModel.path_id == path_id))
        result = await self.session.execute(delete(PathModel).where(PathModel.id == path_id))
        return int(result.rowcount or 0)
