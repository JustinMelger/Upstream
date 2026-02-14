from typing import List, Optional

from fastapi import APIRouter, Depends, Query

from backend.api.deps import get_articles_service, require_session
from backend.api.schemas import ArticleCreateRequest, ArticlePayload
from backend.services.articles_service import ArticlesService


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
