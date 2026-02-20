from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import (
    get_auth_service,
    get_path_recommendations_service,
    get_path_reviews_service,
    get_paths_service,
    get_user_paths_service,
    require_session,
)
from backend.api.policies import (
    require_existing_owner_or_admin,
    require_row_exists,
    require_row_parent_match,
)
from backend.api.schemas.path_recommendations import (
    DeletePathRecommendationResponse,
    PathRecommendationCreateRequest,
    PathRecommendationPayload,
    PathRecommendationSummaryItem,
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
from backend.services.path_recommendations_service import PathRecommendationsService
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


@router.get("/recommendations/summary", response_model=list[PathRecommendationSummaryItem])
async def path_recommendation_summaries(
    path_ids: List[int] = Query(default=[], description="Path IDs to summarize"),
    current_user: str = Depends(require_session),
    recommendations: PathRecommendationsService = Depends(get_path_recommendations_service),
):
    """Return recommendation counts for each path id."""
    return await recommendations.summaries(path_ids=list(path_ids or []))


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
    updated = await user_paths.update_user_path_status(current_user, path_id, payload.status)  # type: ignore[arg-type]

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
    return require_row_exists(await paths.get_path(path_id))


@router.get("/{path_id}/reviews", response_model=list[PathReviewPayload])
async def list_path_reviews(
    path_id: int,
    current_user: str = Depends(require_session),
    paths: PathsService = Depends(get_paths_service),
    reviews: PathReviewsService = Depends(get_path_reviews_service),
):
    """List reviews for a path."""
    require_row_exists(await paths.get_path(path_id))
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
    require_row_exists(await paths.get_path(path_id))
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
    review = require_row_exists(await reviews.get_review_by_id(review_id=int(review_id)))
    require_row_parent_match(row=review, parent_field="path_id", parent_id=int(path_id))
    await require_existing_owner_or_admin(row=review, current_user=current_user, auth=auth)
    deleted = await reviews.delete_review(review_id=int(review_id))
    return {"deleted": bool(deleted)}


@router.get("/{path_id}/recommendations", response_model=list[PathRecommendationPayload])
async def list_path_recommendations(
    path_id: int,
    current_user: str = Depends(require_session),
    paths: PathsService = Depends(get_paths_service),
    recommendations: PathRecommendationsService = Depends(get_path_recommendations_service),
):
    """List recommendations for a path."""
    require_row_exists(await paths.get_path(path_id))
    return await recommendations.list_recommendations(path_id=path_id)


@router.post("/{path_id}/recommendations", response_model=PathRecommendationPayload)
async def create_path_recommendation(
    path_id: int,
    payload: PathRecommendationCreateRequest,
    current_user: str = Depends(require_session),
    paths: PathsService = Depends(get_paths_service),
    recommendations: PathRecommendationsService = Depends(get_path_recommendations_service),
):
    """Create/update current user's recommendation for a path."""
    require_row_exists(await paths.get_path(path_id))
    return await recommendations.create_recommendation(path_id=path_id, payload=payload.model_dump(), created_by=current_user)


@router.delete("/{path_id}/recommendations/{recommendation_id}", response_model=DeletePathRecommendationResponse)
async def delete_path_recommendation(
    path_id: int,
    recommendation_id: int,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    recommendations: PathRecommendationsService = Depends(get_path_recommendations_service),
):
    """Delete a path recommendation (owner/admin only)."""
    recommendation = require_row_exists(
        await recommendations.get_recommendation_by_id(recommendation_id=int(recommendation_id))
    )
    require_row_parent_match(row=recommendation, parent_field="path_id", parent_id=int(path_id))
    await require_existing_owner_or_admin(row=recommendation, current_user=current_user, auth=auth)
    deleted = await recommendations.delete_recommendation(recommendation_id=int(recommendation_id))
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
    await require_existing_owner_or_admin(
        row=await paths.get_path(path_id),
        current_user=current_user,
        auth=auth,
    )

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
    await require_existing_owner_or_admin(
        row=await paths.get_path(path_id),
        current_user=current_user,
        auth=auth,
    )
    return await paths.update_path(path_id, payload.model_dump())
