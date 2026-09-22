from typing import Any

from fastapi import APIRouter, Depends

from backend.api.deps import get_article_reviews_service, get_articles_service, get_auth_service, require_session
from backend.api.policies import require_existing_owner_or_admin, require_row_exists, require_row_parent_match
from backend.api.schemas import (
    ArticleCreateRequest,
    ArticlePayload,
    ArticleReviewCreateRequest,
    ArticleReviewPayload,
    DeleteArticleReviewResponse,
)
from backend.api.schemas.articles import ArticleUpdateRequest
from backend.services.article_reviews_service import ArticleReviewsService
from backend.services.articles_service import ArticlesService
from backend.services.auth_service import AuthService


router = APIRouter(prefix="/articles", tags=["articles"])


@router.post("", response_model=ArticlePayload)
async def create_article(
    payload: ArticleCreateRequest,
    current_user: str = Depends(require_session),
    articles: ArticlesService = Depends(get_articles_service),
) -> dict[str, Any]:
    """Create an article (any authenticated user)."""
    return await articles.create_article(payload=payload.model_dump(exclude_unset=True), created_by=current_user)


@router.get("/{article_id}", response_model=ArticlePayload)
async def get_article(
    article_id: int,
    _current_user: str = Depends(require_session),
    articles: ArticlesService = Depends(get_articles_service),
) -> dict[str, Any]:
    """Get one article by id."""
    return require_row_exists(await articles.get_article_by_id(article_id=int(article_id)))


@router.get("/{article_id}/reviews", response_model=list[ArticleReviewPayload])
async def list_article_reviews(
    article_id: int,
    _current_user: str = Depends(require_session),
    articles: ArticlesService = Depends(get_articles_service),
    reviews: ArticleReviewsService = Depends(get_article_reviews_service),
) -> list[dict[str, Any]]:
    """List reviews for an article."""
    require_row_exists(await articles.get_article_by_id(article_id=int(article_id)))
    return await reviews.list_reviews(article_id=article_id)


@router.post("/{article_id}/reviews", response_model=ArticleReviewPayload)
async def create_article_review(
    article_id: int,
    payload: ArticleReviewCreateRequest,
    current_user: str = Depends(require_session),
    articles: ArticlesService = Depends(get_articles_service),
    reviews: ArticleReviewsService = Depends(get_article_reviews_service),
) -> dict[str, Any]:
    """Create/update current user's review for an article."""
    require_row_exists(await articles.get_article_by_id(article_id=int(article_id)))
    return await reviews.create_review(
        article_id=article_id, payload=payload.model_dump(exclude_unset=True), created_by=current_user
    )


@router.delete("/{article_id}/reviews/{review_id}", response_model=DeleteArticleReviewResponse)
async def delete_article_review(
    article_id: int,
    review_id: int,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    reviews: ArticleReviewsService = Depends(get_article_reviews_service),
) -> dict[str, bool]:
    """Delete an article review (owner or admin)."""
    review = require_row_exists(await reviews.get_review_by_id(review_id=int(review_id)))
    require_row_parent_match(row=review, parent_field="article_id", parent_id=int(article_id))
    await require_existing_owner_or_admin(row=review, current_user=current_user, auth=auth)

    deleted = await reviews.delete_review(review_id=int(review_id))
    return {"deleted": bool(deleted)}


@router.put("/{article_id}", response_model=ArticlePayload)
async def update_article(
    article_id: int,
    payload: ArticleUpdateRequest,
    current_user: str = Depends(require_session),
    articles: ArticlesService = Depends(get_articles_service),
    auth: AuthService = Depends(get_auth_service),
) -> dict:
    """Edit content as its owner or an administrator."""
    await require_existing_owner_or_admin(
        row=await articles.get_article_by_id(article_id=article_id), current_user=current_user, auth=auth
    )
    return require_row_exists(await articles.update_article(article_id, payload.model_dump(exclude_unset=True)))


@router.delete("/{article_id}")
async def delete_article(
    article_id: int,
    current_user: str = Depends(require_session),
    articles: ArticlesService = Depends(get_articles_service),
    auth: AuthService = Depends(get_auth_service),
) -> dict[str, bool]:
    """Delete content and its reviews/path references as owner or admin."""
    await require_existing_owner_or_admin(
        row=await articles.get_article_by_id(article_id=article_id), current_user=current_user, auth=auth
    )
    return {"deleted": await articles.delete_article(article_id)}
