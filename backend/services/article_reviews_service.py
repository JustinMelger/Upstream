from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from pydantic import ValidationError
from pydantic.dataclasses import dataclass

from backend.core.errors import error_handler, F, ServiceError
from backend.database.async_repositories.article_reviews import ArticleReviewsRepository
from backend.database.tx import session_scope
from backend.services.review_upsert import upsert_review_id


class ArticleReviewsServiceError(ServiceError):
    """Domain error for article review failures."""


def article_reviews_error_handler(
    message: str = "An unexpected error occurred while handling article reviews",
    status_code: int = 500,
) -> Callable[[F], F]:
    """Build an error-handler decorator for article review service methods.

    Args:
        message: Default fallback error message.
        status_code: Default HTTP status code for unexpected failures.

    Returns:
        Decorator wrapping uncaught errors as `ArticleReviewsServiceError`.

    """
    return error_handler(
        service_error=ArticleReviewsServiceError,
        message=message,
        status_code=status_code,
        log_message="Article reviews service error",
    )


@dataclass
class ArticleReviewMutationPayload:
    """Typed service-layer payload for article review mutation."""

    rating: int | float | str | None = None
    text: str | None = None


class ArticleReviewsService:
    """Article reviews service."""

    def __init__(self, repo: ArticleReviewsRepository):
        """Initialize the service.

        Args:
            repo: Article reviews repository.

        """
        self._repo = repo

    @staticmethod
    def _coerce_rating(value: int | float | str | None) -> int:
        if value is None:
            raise ArticleReviewsServiceError(detail="invalid_rating", status_code=400)
        try:
            rating_i = int(value)
        except (TypeError, ValueError):
            raise ArticleReviewsServiceError(detail="invalid_rating", status_code=400)
        if rating_i < 1 or rating_i > 5:
            raise ArticleReviewsServiceError(detail="invalid_rating", status_code=400)
        return rating_i

    @article_reviews_error_handler()
    async def list_reviews(self, *, article_id: int) -> list[dict]:
        """List review rows for one article.

        Args:
            article_id: Article identifier.

        Returns:
            Serialized review rows.

        """
        async with session_scope(self._repo.session):
            rows = await self._repo.list_for_article(article_id=article_id)
        return [
            {
                "id": r.id,
                "article_id": r.article_id,
                "rating": r.rating,
                "text": r.text or "",
                "created_by": r.created_by,
                "created_at": r.created_at,
            }
            for r in rows
        ]

    @article_reviews_error_handler()
    async def create_review(self, *, article_id: int, payload: dict, created_by: str) -> dict:
        """Create or update the current user's review for an article."""
        data = self._parse_mutation_payload(payload)
        rating_i = self._coerce_rating(data.rating)

        text = str(data.text or "").strip() or None
        created_at = datetime.now(timezone.utc).isoformat()
        async with session_scope(self._repo.session):
            review_id = await upsert_review_id(
                get_existing=lambda: self._repo.get_review_for_article_by_user(
                    article_id=int(article_id),
                    created_by=str(created_by),
                ),
                create=lambda: self._repo.create_review(
                    article_id=int(article_id),
                    rating=rating_i,
                    text=text,
                    created_by=str(created_by),
                    created_at=created_at,
                ),
                get_concurrent=lambda: self._repo.get_review_for_article_by_user(
                    article_id=int(article_id),
                    created_by=str(created_by),
                ),
                update=lambda review_id: self._repo.update_review(
                    review_id=int(review_id),
                    rating=rating_i,
                    text=text,
                    created_at=created_at,
                ),
            )

        async with session_scope(self._repo.session):
            created = await self._repo.get_review_by_id(int(review_id))
        if not created:
            raise ArticleReviewsServiceError(detail="create_failed", status_code=500)
        return {
            "id": created.id,
            "article_id": created.article_id,
            "rating": created.rating,
            "text": created.text or "",
            "created_by": created.created_by,
            "created_at": created.created_at,
        }

    @staticmethod
    def _parse_mutation_payload(payload: dict) -> ArticleReviewMutationPayload:
        """Parse and validate an article review payload."""
        try:
            return ArticleReviewMutationPayload(**dict(payload or {}))
        except ValidationError as exc:
            raise ArticleReviewsServiceError(detail="invalid_payload", status_code=400) from exc

    @article_reviews_error_handler()
    async def get_review_by_id(self, *, review_id: int) -> dict | None:
        """Fetch a review by id."""
        async with session_scope(self._repo.session):
            row = await self._repo.get_review_by_id(int(review_id))
        if not row:
            return None
        return {
            "id": row.id,
            "article_id": row.article_id,
            "rating": row.rating,
            "text": row.text or "",
            "created_by": row.created_by,
            "created_at": row.created_at,
        }

    @article_reviews_error_handler()
    async def delete_review(self, *, review_id: int) -> bool:
        """Delete a review by id."""
        async with session_scope(self._repo.session):
            deleted = await self._repo.delete_review(review_id=int(review_id))
        return bool(deleted)
