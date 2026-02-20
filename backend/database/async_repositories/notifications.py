from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.async_repositories.datetime_utils import RepositoryDateTimeCodec
from backend.database.orm_models import (
    Article as ArticleModel,
    ArticleReview as ArticleReviewModel,
    Course as CourseModel,
    CourseRecommendation as CourseRecommendationModel,
    CourseReview as CourseReviewModel,
    Path as PathModel,
    PathRecommendation as PathRecommendationModel,
    PathReview as PathReviewModel,
)


class NotificationsRepository(RepositoryDateTimeCodec):
    """Read-only repository for notifications/activity feed data."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_recent_course_share_events(self, *, limit: int) -> list[dict]:
        """Return recent course share rows."""
        result = await self.session.execute(
            select(
                CourseModel.id,
                CourseModel.title,
                CourseModel.created_by,
                CourseModel.created_at,
            )
            .where(CourseModel.created_by.is_not(None))
            .where(CourseModel.created_at.is_not(None))
            .order_by(CourseModel.created_at.desc(), CourseModel.id.desc())
            .limit(int(limit))
        )
        rows = result.all()
        return [
            {
                "course_id": int(r.id),
                "title": str(r.title or ""),
                "created_by": str(r.created_by or ""),
                "created_at": self._as_iso_or_empty(r.created_at),
            }
            for r in rows
            if str(r.created_by or "").strip() and str(r.created_at or "").strip()
        ]

    async def list_recent_course_recommendation_events(self, *, limit: int) -> list[dict]:
        """Return recent course recommendation rows with course owner/title."""
        result = await self.session.execute(
            select(
                CourseRecommendationModel.id,
                CourseRecommendationModel.course_id,
                CourseRecommendationModel.created_by,
                CourseRecommendationModel.created_at,
                CourseModel.title,
                CourseModel.created_by.label("course_owner"),
            )
            .join(CourseModel, CourseModel.id == CourseRecommendationModel.course_id)
            .order_by(CourseRecommendationModel.created_at.desc(), CourseRecommendationModel.id.desc())
            .limit(int(limit))
        )
        rows = result.all()
        return [
            {
                "recommendation_id": int(r.id),
                "course_id": int(r.course_id),
                "created_by": str(r.created_by or ""),
                "created_at": self._as_iso_or_empty(r.created_at),
                "title": str(r.title or ""),
                "course_owner": str(r.course_owner or ""),
            }
            for r in rows
            if str(r.created_by or "").strip() and str(r.created_at or "").strip()
        ]

    async def list_recent_course_recommendation_events_by_user(self, *, created_by: str, limit: int) -> list[dict]:
        """Return recent course recommendation rows created by one user."""
        result = await self.session.execute(
            select(
                CourseRecommendationModel.id,
                CourseRecommendationModel.course_id,
                CourseRecommendationModel.created_by,
                CourseRecommendationModel.created_at,
                CourseModel.title,
                CourseModel.created_by.label("course_owner"),
            )
            .join(CourseModel, CourseModel.id == CourseRecommendationModel.course_id)
            .where(CourseRecommendationModel.created_by == str(created_by))
            .order_by(CourseRecommendationModel.id.desc())
            .limit(int(limit))
        )
        rows = result.all()
        return [
            {
                "recommendation_id": int(r.id),
                "course_id": int(r.course_id),
                "created_by": str(r.created_by or ""),
                "created_at": self._as_iso_or_empty(r.created_at),
                "title": str(r.title or ""),
                "course_owner": str(r.course_owner or ""),
            }
            for r in rows
            if str(r.created_by or "").strip() and str(r.created_at or "").strip()
        ]

    async def list_recent_path_recommendation_events(self, *, limit: int) -> list[dict]:
        """Return recent path recommendation rows with path owner/name."""
        result = await self.session.execute(
            select(
                PathRecommendationModel.id,
                PathRecommendationModel.path_id,
                PathRecommendationModel.created_by,
                PathRecommendationModel.created_at,
                PathModel.name,
                PathModel.created_by.label("path_owner"),
            )
            .join(PathModel, PathModel.id == PathRecommendationModel.path_id)
            .order_by(PathRecommendationModel.created_at.desc(), PathRecommendationModel.id.desc())
            .limit(int(limit))
        )
        rows = result.all()
        return [
            {
                "recommendation_id": int(r.id),
                "path_id": int(r.path_id),
                "created_by": str(r.created_by or ""),
                "created_at": self._as_iso_or_empty(r.created_at),
                "name": str(r.name or ""),
                "path_owner": str(r.path_owner or ""),
            }
            for r in rows
            if str(r.created_by or "").strip() and str(r.created_at or "").strip()
        ]

    async def list_recent_path_recommendation_events_by_user(self, *, created_by: str, limit: int) -> list[dict]:
        """Return recent path recommendation rows created by one user."""
        result = await self.session.execute(
            select(
                PathRecommendationModel.id,
                PathRecommendationModel.path_id,
                PathRecommendationModel.created_by,
                PathRecommendationModel.created_at,
                PathModel.name,
                PathModel.created_by.label("path_owner"),
            )
            .join(PathModel, PathModel.id == PathRecommendationModel.path_id)
            .where(PathRecommendationModel.created_by == str(created_by))
            .order_by(PathRecommendationModel.id.desc())
            .limit(int(limit))
        )
        rows = result.all()
        return [
            {
                "recommendation_id": int(r.id),
                "path_id": int(r.path_id),
                "created_by": str(r.created_by or ""),
                "created_at": self._as_iso_or_empty(r.created_at),
                "name": str(r.name or ""),
                "path_owner": str(r.path_owner or ""),
            }
            for r in rows
            if str(r.created_by or "").strip() and str(r.created_at or "").strip()
        ]

    async def list_recent_course_review_events(self, *, limit: int) -> list[dict]:
        """Return recent course review rows with course owner/title."""
        result = await self.session.execute(
            select(
                CourseReviewModel.id,
                CourseReviewModel.course_id,
                CourseReviewModel.created_by,
                CourseReviewModel.created_at,
                CourseReviewModel.rating,
                CourseModel.title,
                CourseModel.created_by.label("course_owner"),
            )
            .join(CourseModel, CourseModel.id == CourseReviewModel.course_id)
            .order_by(CourseReviewModel.created_at.desc(), CourseReviewModel.id.desc())
            .limit(int(limit))
        )
        rows = result.all()
        return [
            {
                "review_id": int(r.id),
                "course_id": int(r.course_id),
                "created_by": str(r.created_by or ""),
                "created_at": self._as_iso_or_empty(r.created_at),
                "rating": int(r.rating or 0),
                "title": str(r.title or ""),
                "course_owner": str(r.course_owner or ""),
            }
            for r in rows
            if str(r.created_by or "").strip() and str(r.created_at or "").strip()
        ]

    async def list_recent_path_review_events(self, *, limit: int) -> list[dict]:
        """Return recent path review rows with path owner/name."""
        result = await self.session.execute(
            select(
                PathReviewModel.id,
                PathReviewModel.path_id,
                PathReviewModel.created_by,
                PathReviewModel.created_at,
                PathReviewModel.rating,
                PathModel.name,
                PathModel.created_by.label("path_owner"),
            )
            .join(PathModel, PathModel.id == PathReviewModel.path_id)
            .order_by(PathReviewModel.created_at.desc(), PathReviewModel.id.desc())
            .limit(int(limit))
        )
        rows = result.all()
        return [
            {
                "review_id": int(r.id),
                "path_id": int(r.path_id),
                "created_by": str(r.created_by or ""),
                "created_at": self._as_iso_or_empty(r.created_at),
                "rating": int(r.rating or 0),
                "name": str(r.name or ""),
                "path_owner": str(r.path_owner or ""),
            }
            for r in rows
            if str(r.created_by or "").strip() and str(r.created_at or "").strip()
        ]

    async def list_recent_article_review_events(self, *, limit: int) -> list[dict]:
        """Return recent article review rows with article owner/title."""
        result = await self.session.execute(
            select(
                ArticleReviewModel.id,
                ArticleReviewModel.article_id,
                ArticleReviewModel.created_by,
                ArticleReviewModel.created_at,
                ArticleReviewModel.rating,
                ArticleModel.title,
                ArticleModel.created_by.label("article_owner"),
            )
            .join(ArticleModel, ArticleModel.id == ArticleReviewModel.article_id)
            .order_by(ArticleReviewModel.created_at.desc(), ArticleReviewModel.id.desc())
            .limit(int(limit))
        )
        rows = result.all()
        return [
            {
                "review_id": int(r.id),
                "article_id": int(r.article_id),
                "created_by": str(r.created_by or ""),
                "created_at": self._as_iso_or_empty(r.created_at),
                "rating": int(r.rating or 0),
                "title": str(r.title or ""),
                "article_owner": str(r.article_owner or ""),
            }
            for r in rows
            if str(r.created_by or "").strip() and str(r.created_at or "").strip()
        ]
