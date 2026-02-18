from __future__ import annotations

from datetime import datetime, timezone

from backend.core.errors import courses_error_handler, CoursesServiceError
from backend.database.async_repositories.course_recommendations import CourseRecommendationsRepository
from backend.database.async_repositories.courses import CoursesRepository
from backend.database.models import CourseRecommendationRecord, CourseRecord
from backend.services.course_search_document import build_course_search_document


class CoursesService:
    """Course management service."""

    def __init__(
        self,
        repo: CoursesRepository,
        recommendations_repo: CourseRecommendationsRepository | None = None,
    ):
        """Initialize the service.

        Args:
            repo: Persistence repository for courses.
        """
        self._repo = repo
        self._recommendations_repo = recommendations_repo

    @courses_error_handler()
    async def list_courses(
        self,
        *,
        query: str | None = None,
        provider: str | None = None,
        category: str | None = None,
        level: str | None = None,
    ) -> list[dict]:
        """List courses with optional filters.

        Args:
            query: Search query.
            provider: Provider filter.
            category: Category filter.
            level: Level filter.

        Returns:
            Course list payloads.
        """
        recommendation_map: dict[int, list[CourseRecommendationRecord]] = {}
        async with self._repo.session.begin():
            rows = await self._repo.list_courses(query=query, provider=provider, category=category, level=level)
            if self._recommendations_repo and rows:
                recommendation_map = await self._recommendations_repo.list_for_courses(course_ids=[int(r.id) for r in rows])
        return [self._to_payload(row, recommendations=recommendation_map.get(int(row.id), [])) for row in rows]

    @courses_error_handler()
    async def get_course_by_id(self, course_id: int) -> dict | None:
        """Fetch a course by ID.

        Args:
            course_id: Course ID.

        Returns:
            Course payload or None if missing.
        """
        recommendation_rows: list[CourseRecommendationRecord] = []
        async with self._repo.session.begin():
            course = await self._repo.get_course_by_id(course_id)
            if self._recommendations_repo and course:
                recommendation_map = await self._recommendations_repo.list_for_courses(course_ids=[int(course_id)])
                recommendation_rows = recommendation_map.get(int(course_id), [])
        return self._to_payload(course, recommendations=recommendation_rows) if course else None

    @courses_error_handler()
    async def create_course(self, payload: dict) -> dict:
        """Create a new course.

        Args:
            payload: Course payload.

        Returns:
            Created course payload.

        Raises:
            CoursesServiceError: If required fields are missing.
        """
        title = (payload.get("title") or "").strip()
        if not title:
            raise CoursesServiceError(detail="missing_title", status_code=400)

        description = (payload.get("description") or "").strip()
        if not description:
            raise CoursesServiceError(detail="missing_description", status_code=400)

        provider = (payload.get("provider") or "").strip() or None
        category = (payload.get("category") or "").strip() or None
        level = (payload.get("level") or "").strip() or None
        learning_outcomes = (payload.get("learning_outcomes") or "").strip() or None
        prerequisites = (payload.get("prerequisites") or "").strip() or None
        language = (payload.get("language") or "").strip() or None
        url = (payload.get("url") or "").strip() or None
        duration_hours = self._parse_float(payload.get("duration_hours"))
        created_at = datetime.now(timezone.utc).isoformat()
        created_by = (payload.get("created_by") or "").strip() or None

        async with self._repo.session.begin():
            if url:
                duplicate_url = await self._repo.find_course_by_url(url=url)
                if duplicate_url:
                    raise CoursesServiceError(detail="duplicate_url", status_code=409)
            duplicate_title_provider = await self._repo.find_course_by_title_provider(title=title, provider=provider)
            if duplicate_title_provider:
                raise CoursesServiceError(detail="duplicate_title_provider", status_code=409)
            course_id = await self._repo.create_course(
                title=title,
                description=description,
                learning_outcomes=learning_outcomes,
                prerequisites=prerequisites,
                language=language,
                provider=provider,
                category=category,
                level=level,
                duration_hours=duration_hours,
                url=url,
                created_at=created_at,
                created_by=created_by,
            )
        course = await self.get_course_by_id(course_id)
        if not course:
            raise CoursesServiceError(detail="created_course_missing", status_code=500)
        return course

    @courses_error_handler()
    async def update_course(self, course_id: int, payload: dict) -> dict | None:
        """Update a course by ID.

        Args:
            course_id: Course ID.
            payload: Updates payload.

        Returns:
            Updated course payload or None if missing.
        """
        async with self._repo.session.begin():
            existing = await self._repo.get_course_by_id(course_id)
        if not existing:
            return None

        title = (payload.get("title") or existing.title).strip()
        description = (payload.get("description") or existing.description).strip()
        if not description:
            raise CoursesServiceError(detail="missing_description", status_code=400)
        provider = (payload.get("provider") or (existing.provider or "")).strip() or None
        category = (payload.get("category") or (existing.category or "")).strip() or None
        level = (payload.get("level") or (existing.level or "")).strip() or None
        learning_outcomes = (payload.get("learning_outcomes") or (existing.learning_outcomes or "")).strip() or None
        prerequisites = (payload.get("prerequisites") or (existing.prerequisites or "")).strip() or None
        language = (payload.get("language") or (existing.language or "")).strip() or None
        url = (payload.get("url") or (existing.url or "")).strip() or None
        duration_hours = self._parse_float(payload.get("duration_hours"))
        if duration_hours is None:
            duration_hours = existing.duration_hours

        async with self._repo.session.begin():
            await self._repo.update_course(
                course_id=course_id,
                title=title,
                description=description,
                learning_outcomes=learning_outcomes,
                prerequisites=prerequisites,
                language=language,
                provider=provider,
                category=category,
                level=level,
                duration_hours=duration_hours,
                url=url,
            )
        return await self.get_course_by_id(course_id)

    @courses_error_handler()
    async def delete_course(self, course_id: int) -> bool:
        """Delete a course by ID.

        Args:
            course_id: Course ID.

        Returns:
            True if deleted.
        """
        async with self._repo.session.begin():
            return (await self._repo.delete_course(course_id)) > 0

    @staticmethod
    def _parse_float(value):
        """Parse a float value or return None."""
        try:
            return float(value) if value not in (None, "") else None
        except ValueError:
            return None

    @staticmethod
    def _to_payload(course: CourseRecord, *, recommendations: list[CourseRecommendationRecord] | None = None) -> dict:
        """Convert a course record to an API payload."""
        rec_rows = list(recommendations or [])
        rec_notes = [str(r.note or "") for r in rec_rows if str(r.note or "").strip()]
        rec_by = [str(r.created_by or "") for r in rec_rows if str(r.created_by or "").strip()]
        return {
            "id": course.id,
            "title": course.title or "",
            "description": course.description or "",
            "learning_outcomes": course.learning_outcomes or "",
            "prerequisites": course.prerequisites or "",
            "language": course.language or "",
            "provider": course.provider or "",
            "category": course.category or "",
            "level": course.level or "",
            "duration_hours": course.duration_hours,
            "url": course.url or "",
            "created_at": course.created_at,
            "created_by": course.created_by,
            "search_document": build_course_search_document(
                course=course,
                recommendation_count=len(rec_rows),
                recommendation_notes=rec_notes,
                recommended_by=rec_by,
            ),
        }
