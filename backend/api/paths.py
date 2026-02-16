from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import (
    get_auth_service,
    get_path_reviews_service,
    get_paths_service,
    get_user_paths_service,
    require_session,
)
from backend.api.schemas.path_reviews import (
    DeletePathReviewResponse,
    PathReviewCreateRequest,
    PathReviewPayload,
    PathReviewSummaryItem,
)
from backend.api.schemas.paths import (
    DeletePathResponse,
    PathCreateRequest,
    PathDetailResponse,
    PathListItem,
    PathStatusRequest,
    PathStatusResponse,
    PathUpdateRequest,
    SelectedPathItem,
    SelectPathResponse,
    UnselectPathResponse,
)
from backend.services.auth_service import AuthService
from backend.services.path_reviews_service import PathReviewsService
from backend.services.paths_service import PathsService
from backend.services.user_paths_service import UserPathsService


router = APIRouter(prefix="/paths", tags=["paths"])


@router.get("", response_model=List[PathListItem])
async def list_paths(
    current_user: str = Depends(require_session),
    paths: PathsService = Depends(get_paths_service),
):
    """List all learning paths.

    Args:
        current_user: Authenticated username.

    Returns:
        list[dict]: Path list.
    """
    return await paths.list_paths()


@router.get("/reviews/summary", response_model=list[PathReviewSummaryItem])
async def path_review_summaries(
    path_ids: List[int] = Query(default=[], description="Path IDs to summarize"),
    current_user: str = Depends(require_session),
    reviews: PathReviewsService = Depends(get_path_reviews_service),
):
    """Return average rating + count for each path id."""
    return await reviews.summaries(path_ids=list(path_ids or []))


@router.post("", response_model=PathDetailResponse)
async def add_path(
    payload: PathCreateRequest,
    current_user: str = Depends(require_session),
    paths: PathsService = Depends(get_paths_service),
):
    """Create a learning path (any authenticated user).

    Args:
        payload: Path payload.
        current_user: Authenticated username.

    Returns:
        dict: Created path.
    """
    data = payload.model_dump()
    data["created_by"] = current_user
    return await paths.create_path(data)


@router.post("/{path_id}/select", response_model=SelectPathResponse)
async def select_path(
    path_id: int,
    current_user: str = Depends(require_session),
    user_paths: UserPathsService = Depends(get_user_paths_service),
):
    """Add a path to the current user's selections.

    Args:
        path_id: Path ID.
        current_user: Authenticated username.

    Returns:
        dict: Selection result.
    """
    return await user_paths.add_user_path(current_user, path_id)


@router.post("/{path_id}/unselect", response_model=UnselectPathResponse)
async def unselect_path(
    path_id: int,
    current_user: str = Depends(require_session),
    user_paths: UserPathsService = Depends(get_user_paths_service),
):
    """Remove a path from the current user's selections.

    Args:
        path_id: Path ID.
        current_user: Authenticated username.

    Returns:
        dict: Removal result.
    """
    removed = await user_paths.remove_user_path(current_user, path_id)
    if removed == 0:
        raise HTTPException(status_code=404, detail="path_not_selected")
    return {"removed": removed}


@router.post("/{path_id}/status", response_model=PathStatusResponse)
async def set_path_status(
    path_id: int,
    payload: PathStatusRequest,
    current_user: str = Depends(require_session),
    user_paths: UserPathsService = Depends(get_user_paths_service),
):
    """Update the status for a selected path.

    Args:
        path_id: Path ID.
        payload: Status payload.
        current_user: Authenticated username.

    Returns:
        dict: Update result.
    """
    status = (payload.status or "").strip()
    if not status:
        raise HTTPException(status_code=400, detail="missing_fields")

    updated = await user_paths.update_user_path_status(current_user, path_id, status)

    if updated == 0:
        raise HTTPException(status_code=404, detail="path_not_selected")

    return {"updated": updated}


@router.get("/selected/list", response_model=list[SelectedPathItem])
async def list_selected_paths(
    current_user: str = Depends(require_session),
    user_paths: UserPathsService = Depends(get_user_paths_service),
):
    """List paths selected by the current user.

    Args:
        current_user: Authenticated username.

    Returns:
        list[dict]: Selected paths.
    """
    return await user_paths.list_user_paths(current_user)


@router.get("/{path_id}", response_model=PathDetailResponse)
async def get_path(
    path_id: int,
    current_user: str = Depends(require_session),
    paths: PathsService = Depends(get_paths_service),
):
    """Get a learning path by ID.

    Args:
        path_id: Path ID.
        current_user: Authenticated username.

    Returns:
        dict: Path payload.
    """
    path = await paths.get_path(path_id)
    if not path:
        raise HTTPException(status_code=404, detail="not_found")
    return path


@router.get("/{path_id}/reviews", response_model=list[PathReviewPayload])
async def list_path_reviews(
    path_id: int,
    current_user: str = Depends(require_session),
    paths: PathsService = Depends(get_paths_service),
    reviews: PathReviewsService = Depends(get_path_reviews_service),
):
    """List reviews for a path."""
    existing = await paths.get_path(path_id)
    if not existing:
        raise HTTPException(status_code=404, detail="not_found")
    return await reviews.list_reviews(path_id=path_id)


@router.post("/{path_id}/reviews", response_model=PathReviewPayload)
async def create_path_review(
    path_id: int,
    payload: PathReviewCreateRequest,
    current_user: str = Depends(require_session),
    paths: PathsService = Depends(get_paths_service),
    reviews: PathReviewsService = Depends(get_path_reviews_service),
):
    """Create a review for a path (any authenticated user)."""
    existing = await paths.get_path(path_id)
    if not existing:
        raise HTTPException(status_code=404, detail="not_found")
    return await reviews.create_review(path_id=path_id, payload=payload.model_dump(), created_by=current_user)


@router.delete("/{path_id}/reviews/{review_id}", response_model=DeletePathReviewResponse)
async def delete_path_review(
    path_id: int,
    review_id: int,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    reviews: PathReviewsService = Depends(get_path_reviews_service),
):
    """Delete a path review (owner/admin only)."""
    review = await reviews.get_review_by_id(review_id=int(review_id))
    if not review:
        raise HTTPException(status_code=404, detail="not_found")
    if int(review.get("path_id") or 0) != int(path_id):
        raise HTTPException(status_code=404, detail="not_found")
    if not await auth.is_admin(current_user) and str(review.get("created_by") or "") != str(current_user):
        raise HTTPException(status_code=403, detail="forbidden")
    deleted = await reviews.delete_review(review_id=int(review_id))
    return {"deleted": bool(deleted)}


@router.delete("/{path_id}", response_model=DeletePathResponse)
async def remove_path(
    path_id: int,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    paths: PathsService = Depends(get_paths_service),
):
    """Delete a learning path (owner/admin only).

    Args:
        path_id: Path ID.
        current_user: Authenticated username.

    Returns:
        dict: Delete result.
    """
    if not await auth.is_admin(current_user):
        existing = await paths.get_path(path_id)
        if not existing:
            raise HTTPException(status_code=404, detail="not_found")
        if str(existing.get("created_by") or "") != str(current_user):
            raise HTTPException(status_code=403, detail="forbidden")

    deleted = await paths.delete_path(path_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="not_found")
    return {"deleted": deleted}


@router.put("/{path_id}", response_model=PathDetailResponse)
async def edit_path(
    path_id: int,
    payload: PathUpdateRequest,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    paths: PathsService = Depends(get_paths_service),
):
    """Update a learning path (owner/admin only).

    Args:
        path_id: Path ID.
        payload: Path updates.
        current_user: Authenticated username.

    Returns:
        dict: Updated path.
    """
    if not await auth.is_admin(current_user):
        existing = await paths.get_path(path_id)
        if not existing:
            raise HTTPException(status_code=404, detail="not_found")
        if str(existing.get("created_by") or "") != str(current_user):
            raise HTTPException(status_code=403, detail="forbidden")
    return await paths.update_path(path_id, payload.model_dump())
