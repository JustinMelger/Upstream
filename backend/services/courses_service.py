from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError
from pydantic.dataclasses import dataclass

from backend.core.errors import courses_error_handler, CoursesServiceError
from backend.database.async_repositories.course_recommendations import CourseRecommendationsRepository
from backend.database.async_repositories.courses import CoursesRepository
from backend.database.models import CourseRecommendationRecord, CourseRecord
from backend.database.tx import session_scope
from backend.services.course_search_document import build_course_search_document
from backend.services.url_preview_service import UrlPreviewService


@dataclass
class CourseMutationPayload:
    """Typed service-layer payload for create/update course flows."""

    title: str | None = None
    description: str | None = None
    learning_outcomes: str | None = None
    prerequisites: str | None = None
    language: str | None = None
    provider: str | None = None
    category: str | None = None
    level: str | None = None
    duration_hours: float | int | str | None = None
    url: str | None = None
    created_by: str | None = None


class CoursesService:
    """Course management service."""

    def __init__(
        self,
        repo: CoursesRepository,
        recommendations_repo: CourseRecommendationsRepository | None = None,
        url_preview_service: UrlPreviewService | None = None,
    ):
        """Initialize the service.

        Args:
            repo: Persistence repository for courses.
        """
        self._repo = repo
        self._recommendations_repo = recommendations_repo
        self._url_preview_service = url_preview_service or UrlPreviewService()

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
        async with session_scope(self._repo.session):
            rows = await self._repo.list_courses(query=query, provider=provider, category=category, level=level)
            if self._recommendations_repo and rows:
                recommendation_map = await self._recommendations_repo.list_for_courses(course_ids=[int(r.id) for r in rows])
        preview_map = await self._resolve_preview_images(rows)
        return [
            self._to_payload(
                row,
                recommendations=recommendation_map.get(int(row.id), []),
                preview_image_url=preview_map.get(int(row.id), ""),
            )
            for row in rows
        ]

    @courses_error_handler()
    async def get_course_by_id(self, course_id: int) -> dict | None:
        """Fetch a course by ID.

        Args:
            course_id: Course ID.

        Returns:
            Course payload or None if missing.
        """
        recommendation_rows: list[CourseRecommendationRecord] = []
        async with session_scope(self._repo.session):
            course = await self._repo.get_course_by_id(course_id)
            if self._recommendations_repo and course:
                recommendation_map = await self._recommendations_repo.list_for_courses(course_ids=[int(course_id)])
                recommendation_rows = recommendation_map.get(int(course_id), [])
        if not course:
            return None
        preview_map = await self._resolve_preview_images([course])
        return self._to_payload(
            course,
            recommendations=recommendation_rows,
            preview_image_url=preview_map.get(int(course.id), ""),
        )

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
        data = self._parse_mutation_payload(payload)
        title = str(data.title or "").strip()
        if not title:
            raise CoursesServiceError(detail="missing_title", status_code=400)

        description = str(data.description or "").strip()
        if not description:
            raise CoursesServiceError(detail="missing_description", status_code=400)

        provider = str(data.provider or "").strip() or None
        category = str(data.category or "").strip() or None
        level = str(data.level or "").strip() or None
        learning_outcomes = str(data.learning_outcomes or "").strip() or None
        prerequisites = str(data.prerequisites or "").strip() or None
        language = str(data.language or "").strip() or None
        url = str(data.url or "").strip() or None
        duration_hours = self._parse_float(data.duration_hours)
        created_at = datetime.now(timezone.utc).isoformat()
        created_by = str(data.created_by or "").strip() or None

        async with session_scope(self._repo.session):
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
        data = self._parse_mutation_payload(payload)
        async with session_scope(self._repo.session):
            existing = await self._repo.get_course_by_id(course_id)
        if not existing:
            return None

        title = str(data.title if data.title is not None else existing.title).strip()
        description = str(data.description if data.description is not None else existing.description).strip()
        if not description:
            raise CoursesServiceError(detail="missing_description", status_code=400)
        provider = str(data.provider if data.provider is not None else (existing.provider or "")).strip() or None
        category = str(data.category if data.category is not None else (existing.category or "")).strip() or None
        level = str(data.level if data.level is not None else (existing.level or "")).strip() or None
        learning_outcomes = (
            str(data.learning_outcomes if data.learning_outcomes is not None else (existing.learning_outcomes or "")).strip()
            or None
        )
        prerequisites = (
            str(data.prerequisites if data.prerequisites is not None else (existing.prerequisites or "")).strip() or None
        )
        language = str(data.language if data.language is not None else (existing.language or "")).strip() or None
        url = str(data.url if data.url is not None else (existing.url or "")).strip() or None
        duration_hours = self._parse_float(data.duration_hours)
        if duration_hours is None:
            duration_hours = existing.duration_hours

        async with session_scope(self._repo.session):
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
        async with session_scope(self._repo.session):
            return (await self._repo.delete_course(course_id)) > 0

    @staticmethod
    def _parse_float(value: Any) -> float | None:
        """Parse a float value or return None."""
        try:
            return float(value) if value not in (None, "") else None
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_mutation_payload(payload: dict) -> CourseMutationPayload:
        """Parse and validate a course mutation payload."""
        try:
            return CourseMutationPayload(**dict(payload or {}))
        except ValidationError as exc:
            raise CoursesServiceError(detail="invalid_payload", status_code=400) from exc

    @staticmethod
    def _to_payload(
        course: CourseRecord,
        *,
        recommendations: list[CourseRecommendationRecord] | None = None,
        preview_image_url: str = "",
    ) -> dict:
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
            "preview_image_url": str(preview_image_url or ""),
            "created_at": course.created_at,
            "created_by": course.created_by,
            "search_document": build_course_search_document(
                course=course,
                recommendation_count=len(rec_rows),
                recommendation_notes=rec_notes,
                recommended_by=rec_by,
            ),
        }

    async def _resolve_preview_images(self, courses: list[CourseRecord]) -> dict[int, str]:
        out: dict[int, str] = {}
        if not courses:
            return out
        urls: dict[str, list[int]] = {}
        for row in courses:
            course_id = int(getattr(row, "id", 0) or 0)
            url = str(getattr(row, "url", "") or "").strip()
            if course_id <= 0 or not url:
                continue
            urls.setdefault(url, []).append(course_id)
        if not urls:
            return out

        resolved = await asyncio.gather(
            *(self._url_preview_service.resolve_image_url(source_url=url) for url in urls.keys()),
            return_exceptions=True,
        )
        for url, image_url in zip(urls.keys(), resolved, strict=False):
            image = "" if isinstance(image_url, Exception) else str(image_url or "")
            for course_id in urls.get(url, []):
                out[int(course_id)] = image
        return out
