from typing import List, Optional

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
):
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
):
    """Create or update tracking status for a course.

    Args:
        payload: Tracking payload with course_id and status.
        current_user: Authenticated username.

    Returns:
        dict: Tracking record.
    """
    colleague_id = current_user
    course_id = payload.course_id
    status = (payload.status or "").strip()

    if not course_id or not status:
        raise HTTPException(status_code=400, detail="missing_fields")

    try:
        course_id_int = int(course_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_course_id")

    return await tracking.upsert_tracking(colleague_id, course_id_int, status)


@router.post("/delete", response_model=TrackingDeleteResponse)
async def delete_tracking(
    payload: TrackingDeleteRequest,
    current_user: str = Depends(require_session),
    tracking: TrackingService = Depends(get_tracking_service),
):
    """Remove tracking status for a course.

    Args:
        payload: Delete payload with course_id.
        current_user: Authenticated username.

    Returns:
        dict: Delete result.
    """
    colleague_id = current_user
    course_id = payload.course_id

    if not course_id:
        raise HTTPException(status_code=400, detail="missing_fields")

    try:
        course_id_int = int(course_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_course_id")

    removed = await tracking.remove_tracking(colleague_id, course_id_int)
    if removed == 0:
        raise HTTPException(status_code=404, detail="not_found")
    return {"removed": removed}


@router.get("/stats", response_model=dict[str, int])
async def get_stats(
    colleague_id: Optional[str] = Query(default=None),
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    tracking: TrackingService = Depends(get_tracking_service),
):
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
    raise HTTPException(status_code=403, detail="admin_required")


@router.get("/stats/users", response_model=list[TrackingStatsByUserItem])
async def get_stats_by_user(
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    tracking: TrackingService = Depends(get_tracking_service),
):
    """Return tracking stats grouped by user (admin only).

    Args:
        current_user: Authenticated username.

    Returns:
        list[dict]: Stats by user.
    """
    if not await auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")
    return await tracking.stats_by_user()


@router.get("/recent", response_model=list[TrackingRecordPayload])
async def get_recent_activity(
    limit: int = Query(default=10),
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    tracking: TrackingService = Depends(get_tracking_service),
):
    """Return recent activity for the team (admin only).

    Args:
        limit: Max number of records.
        current_user: Authenticated username.

    Returns:
        list[dict]: Recent activity records.
    """
    if not await auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")
    return await tracking.list_recent_activity(limit=limit)
