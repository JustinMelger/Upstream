from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import get_videos_service, require_session
from backend.api.schemas import VideoCreateRequest, VideoPayload
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
