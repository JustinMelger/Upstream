from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import get_auth_service, get_tracking_service, require_session
from backend.api.schemas import (
    TrackingDeleteRequest,
    TrackingDeleteResponse,
    TrackingRecordPayload,
    TrackingStatsByUserItem,
    TrackingUpsertRequest,
)
from backend.services.auth_service import AuthService
from backend.services.tracking_service import TrackingService


router = APIRouter(prefix="/tracking", tags=["tracking"])


@router.get("", response_model=List[TrackingRecordPayload])
async def get_tracking(
    colleague_id: Optional[str] = Query(default=None),
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    tracking: TrackingService = Depends(get_tracking_service),
) -> list[dict[str, Any]]:
    """List tracking entries for a colleague.

    Args:
        colleague_id: Optional colleague username to query.
        current_user: Authenticated username.

    Returns:
        list[dict]: Tracking entries.
    """
    target = colleague_id or current_user
    if target != current_user and not await auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")
    return await tracking.list_tracking(colleague_id=target)


@router.post("", response_model=TrackingRecordPayload)
async def set_tracking(
    payload: TrackingUpsertRequest,
    current_user: str = Depends(require_session),
    tracking: TrackingService = Depends(get_tracking_service),
) -> dict[str, Any]:
    """Create or update tracking status for a course.

    Args:
        payload: Tracking payload with course_id and status.
        current_user: Authenticated username.

    Returns:
        dict: Tracking record.
    """
    return await tracking.upsert_tracking(current_user, payload.course_id, payload.status)  # type: ignore[arg-type]


@router.post("/delete", response_model=TrackingDeleteResponse)
async def delete_tracking(
    payload: TrackingDeleteRequest,
    current_user: str = Depends(require_session),
    tracking: TrackingService = Depends(get_tracking_service),
) -> dict[str, int]:
    """Remove tracking status for a course.

    Args:
        payload: Delete payload with course_id.
        current_user: Authenticated username.

    Returns:
        dict: Delete result.
    """
    removed = await tracking.remove_tracking(current_user, payload.course_id)  # type: ignore[arg-type]
    if removed == 0:
        raise HTTPException(status_code=404, detail="not_found")
    return {"removed": removed}


@router.get("/stats", response_model=dict[str, int])
async def get_stats(
    colleague_id: Optional[str] = Query(default=None),
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    tracking: TrackingService = Depends(get_tracking_service),
) -> dict[str, int]:
    """Return tracking stats for a colleague or team totals.

    Args:
        colleague_id: Optional colleague username to query.
        current_user: Authenticated username.

    Returns:
        dict: Stats payload.
    """
    if colleague_id and colleague_id != current_user and not await auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")
    if colleague_id:
        return await tracking.stats_for_colleague(colleague_id)
    if await auth.is_admin(current_user):
        return await tracking.stats_all()
    return await tracking.stats_for_workspace(current_user)


@router.get("/stats/users", response_model=list[TrackingStatsByUserItem])
async def get_stats_by_user(
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    tracking: TrackingService = Depends(get_tracking_service),
) -> list[dict[str, Any]]:
    """Return tracking stats grouped by user for authenticated users.

    Args:
        current_user: Authenticated username.

    Returns:
        list[dict]: Stats by user.
    """
    if await auth.is_admin(current_user):
        return await tracking.stats_by_user()
    return await tracking.stats_by_workspace_user(current_user)


@router.get("/recent", response_model=list[TrackingRecordPayload])
async def get_recent_activity(
    limit: int = Query(default=10),
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    tracking: TrackingService = Depends(get_tracking_service),
) -> list[dict[str, Any]]:
    """Return recent tracking activity (admin only).

    Args:
        limit: Max number of records.
        current_user: Authenticated username.

    Returns:
        list[dict]: Recent activity records.
    """
    if not await auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")
    return await tracking.list_recent_activity(limit=limit)
