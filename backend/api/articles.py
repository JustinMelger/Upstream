from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import get_article_reviews_service, get_articles_service, get_auth_service, require_session
from backend.api.schemas import (
    ArticleCreateRequest,
    ArticlePayload,
    ArticleReviewCreateRequest,
    ArticleReviewPayload,
    ArticleReviewSummaryItem,
    DeleteArticleReviewResponse,
)
from backend.services.article_reviews_service import ArticleReviewsService
from backend.services.articles_service import ArticlesService
from backend.services.auth_service import AuthService


router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=List[ArticlePayload])
async def list_articles(
    q: Optional[str] = Query(default=None, description="Search query"),
    tag: Optional[str] = Query(default=None, description="Tag filter"),
    current_user: str = Depends(require_session),
    articles: ArticlesService = Depends(get_articles_service),
):
    """List articles."""
    return await articles.list_articles(query=q, tag=tag)


@router.post("", response_model=ArticlePayload)
async def create_article(
    payload: ArticleCreateRequest,
    current_user: str = Depends(require_session),
    articles: ArticlesService = Depends(get_articles_service),
):
    """Create an article (any authenticated user)."""
    return await articles.create_article(payload=payload.model_dump(), created_by=current_user)


@router.get("/reviews/summary", response_model=list[ArticleReviewSummaryItem])
async def article_review_summaries(
    article_ids: list[int] = Query(default_factory=list),
    current_user: str = Depends(require_session),
    reviews: ArticleReviewsService = Depends(get_article_reviews_service),
):
    """Get review summaries for a list of article ids."""
    return await reviews.summaries(article_ids=list(article_ids or []))


@router.get("/{article_id}/reviews", response_model=list[ArticleReviewPayload])
async def list_article_reviews(
    article_id: int,
    current_user: str = Depends(require_session),
    reviews: ArticleReviewsService = Depends(get_article_reviews_service),
):
    """List reviews for an article."""
    return await reviews.list_reviews(article_id=article_id)


@router.post("/{article_id}/reviews", response_model=ArticleReviewPayload)
async def create_article_review(
    article_id: int,
    payload: ArticleReviewCreateRequest,
    current_user: str = Depends(require_session),
    reviews: ArticleReviewsService = Depends(get_article_reviews_service),
):
    """Create/update current user's review for an article."""
    return await reviews.create_review(article_id=article_id, payload=payload.model_dump(), created_by=current_user)


@router.delete("/{article_id}/reviews/{review_id}", response_model=DeleteArticleReviewResponse)
async def delete_article_review(
    article_id: int,
    review_id: int,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    reviews: ArticleReviewsService = Depends(get_article_reviews_service),
):
    """Delete an article review (owner or admin)."""
    review = await reviews.get_review_by_id(review_id=int(review_id))
    if not review or int(review.get("article_id") or 0) != int(article_id):
        raise HTTPException(status_code=404, detail="not_found")

    if not await auth.is_admin(current_user) and str(review.get("created_by") or "") != str(current_user):
        raise HTTPException(status_code=403, detail="forbidden")

    deleted = await reviews.delete_review(review_id=int(review_id))
    return {"deleted": bool(deleted)}
