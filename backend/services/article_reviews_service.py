from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from backend.core.errors import error_handler, ServiceError
from backend.database.async_repositories.article_reviews import ArticleReviewsRepository


class ArticleReviewsServiceError(ServiceError):
    """Domain error for article review failures."""


def article_reviews_error_handler(
    message: str = "An unexpected error occurred while handling article reviews",
    status_code: int = 500,
):
    return error_handler(
        service_error=ArticleReviewsServiceError,
        message=message,
        status_code=status_code,
        log_message="Article reviews service error",
    )


class ArticleReviewsService:
    """Article reviews service."""

    def __init__(self, repo: ArticleReviewsRepository):
        self._repo = repo

    @article_reviews_error_handler()
    async def list_reviews(self, *, article_id: int) -> list[dict]:
        async with self._repo.session.begin():
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
        rating = payload.get("rating")
        try:
            rating_i = int(rating)
        except (TypeError, ValueError):
            raise ArticleReviewsServiceError(detail="invalid_rating", status_code=400)
        if rating_i < 1 or rating_i > 5:
            raise ArticleReviewsServiceError(detail="invalid_rating", status_code=400)

        text = str(payload.get("text") or "").strip() or None
        created_at = datetime.now(timezone.utc).isoformat()

        review_id: int | None = None
        async with self._repo.session.begin():
            existing = await self._repo.get_review_for_article_by_user(article_id=int(article_id), created_by=str(created_by))
            if existing:
                await self._repo.update_review(review_id=existing.id, rating=rating_i, text=text, created_at=created_at)
                review_id = existing.id
            else:
                try:
                    review_id = await self._repo.create_review(
                        article_id=int(article_id),
                        rating=rating_i,
                        text=text,
                        created_by=str(created_by),
                        created_at=created_at,
                    )
                except IntegrityError:
                    concurrent = await self._repo.get_review_for_article_by_user(
                        article_id=int(article_id), created_by=str(created_by)
                    )
                    if not concurrent:
                        raise
                    await self._repo.update_review(
                        review_id=concurrent.id,
                        rating=rating_i,
                        text=text,
                        created_at=created_at,
                    )
                    review_id = concurrent.id

        async with self._repo.session.begin():
            created = await self._repo.get_review_by_id(int(review_id or 0))
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

    @article_reviews_error_handler()
    async def get_review_by_id(self, *, review_id: int) -> dict | None:
        """Fetch a review by id."""
        async with self._repo.session.begin():
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
        async with self._repo.session.begin():
            deleted = await self._repo.delete_review(review_id=int(review_id))
        return bool(deleted)

    @article_reviews_error_handler()
    async def summaries(self, *, article_ids: list[int]) -> list[dict]:
        """Return review summaries for the given article ids."""
        unique_ids: list[int] = []
        seen: set[int] = set()
        for aid in list(article_ids or []):
            try:
                aid_i = int(aid)
            except (TypeError, ValueError):
                continue
            if aid_i <= 0 or aid_i in seen:
                continue
            seen.add(aid_i)
            unique_ids.append(aid_i)

        async with self._repo.session.begin():
            summary_map = await self._repo.summaries_for_articles(article_ids=unique_ids)

        out: list[dict] = []
        for aid in unique_ids:
            avg, count = summary_map.get(aid, (0.0, 0))
            out.append({"article_id": aid, "avg_rating": float(avg), "review_count": int(count)})
        return out
