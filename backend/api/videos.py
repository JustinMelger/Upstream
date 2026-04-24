from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import get_auth_service, get_video_reviews_service, get_videos_service, require_session
from backend.api.policies import require_existing_owner_or_admin, require_row_exists, require_row_parent_match
from backend.api.schemas import (
    DeleteVideoReviewResponse,
    VideoCreateRequest,
    VideoPayload,
    VideoReviewCreateRequest,
    VideoReviewPayload,
    VideoReviewSummaryItem,
)
from backend.services.auth_service import AuthService
from backend.services.video_reviews_service import VideoReviewsService
from backend.services.videos_service import VideosService


router = APIRouter(prefix="/videos", tags=["videos"])


@router.get("", response_model=List[VideoPayload])
async def list_videos(
    q: Optional[str] = Query(default=None, description="Search query"),
    provider: Optional[str] = Query(default=None, description="Provider filter"),
    category: Optional[str] = Query(default=None, description="Category filter"),
    current_user: str = Depends(require_session),
    videos: VideosService = Depends(get_videos_service),
) -> list[dict[str, Any]]:
    """List videos."""
    _ = current_user
    return await videos.list_videos(query=q, provider=provider, category=category)


@router.get("/reviews/summary", response_model=list[VideoReviewSummaryItem])
async def video_review_summaries(
    video_ids: list[int] = Query(default_factory=list),
    current_user: str = Depends(require_session),
    reviews: VideoReviewsService = Depends(get_video_reviews_service),
) -> list[dict[str, Any]]:
    """Get review summaries for a list of video ids."""
    _ = current_user
    return await reviews.summaries(video_ids=list(video_ids or []))


@router.get("/{video_id}", response_model=VideoPayload)
async def get_video(
    video_id: int,
    current_user: str = Depends(require_session),
    videos: VideosService = Depends(get_videos_service),
) -> dict[str, Any]:
    """Get one video by id."""
    _ = current_user
    video = await videos.get_video_by_id(video_id=int(video_id))
    if not video:
        raise HTTPException(status_code=404, detail="not_found")
    return video


@router.post("", response_model=VideoPayload)
async def create_video(
    payload: VideoCreateRequest,
    current_user: str = Depends(require_session),
    videos: VideosService = Depends(get_videos_service),
) -> dict[str, Any]:
    """Create a video."""
    return await videos.create_video(payload=payload.model_dump(), created_by=current_user)


@router.get("/{video_id}/reviews", response_model=list[VideoReviewPayload])
async def list_video_reviews(
    video_id: int,
    current_user: str = Depends(require_session),
    videos: VideosService = Depends(get_videos_service),
    reviews: VideoReviewsService = Depends(get_video_reviews_service),
) -> list[dict[str, Any]]:
    """List reviews for a video."""
    _ = current_user
    require_row_exists(await videos.get_video_by_id(video_id=int(video_id)))
    return await reviews.list_reviews(video_id=video_id)


@router.post("/{video_id}/reviews", response_model=VideoReviewPayload)
async def create_video_review(
    video_id: int,
    payload: VideoReviewCreateRequest,
    current_user: str = Depends(require_session),
    videos: VideosService = Depends(get_videos_service),
    reviews: VideoReviewsService = Depends(get_video_reviews_service),
) -> dict[str, Any]:
    """Create/update current user's review for a video."""
    require_row_exists(await videos.get_video_by_id(video_id=int(video_id)))
    return await reviews.create_review(video_id=video_id, payload=payload.model_dump(), created_by=current_user)


@router.delete("/{video_id}/reviews/{review_id}", response_model=DeleteVideoReviewResponse)
async def delete_video_review(
    video_id: int,
    review_id: int,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    reviews: VideoReviewsService = Depends(get_video_reviews_service),
) -> dict[str, bool]:
    """Delete a video review (owner or admin)."""
    review = require_row_exists(await reviews.get_review_by_id(review_id=int(review_id)))
    require_row_parent_match(row=review, parent_field="video_id", parent_id=int(video_id))
    await require_existing_owner_or_admin(row=review, current_user=current_user, auth=auth)

    deleted = await reviews.delete_review(review_id=int(review_id))
    return {"deleted": bool(deleted)}
