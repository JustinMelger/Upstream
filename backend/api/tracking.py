from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import require_session
from backend.services.auth_service import auth_service
from backend.services.tracking_service import (
    list_recent_activity,
    list_tracking,
    remove_tracking,
    stats_all,
    stats_by_user,
    stats_for_colleague,
    upsert_tracking,
)


router = APIRouter(prefix="/tracking", tags=["tracking"])


@router.get("", response_model=List[dict])
def get_tracking(
    colleague_id: Optional[str] = Query(default=None),
    current_user: str = Depends(require_session),
):
    """List tracking entries for a colleague.

    Args:
        colleague_id: Optional colleague username to query.
        current_user: Authenticated username.

    Returns:
        list[dict]: Tracking entries.
    """
    target = colleague_id or current_user
    if target != current_user and not auth_service.is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")
    return list_tracking(colleague_id=target)


@router.post("", response_model=dict)
def set_tracking(payload: dict, current_user: str = Depends(require_session)):
    """Create or update tracking status for a course.

    Args:
        payload: Tracking payload with course_id and status.
        current_user: Authenticated username.

    Returns:
        dict: Tracking record.
    """
    colleague_id = current_user
    course_id = payload.get("course_id")
    status = (payload.get("status") or "").strip()

    if not course_id or not status:
        raise HTTPException(status_code=400, detail="missing_fields")

    try:
        course_id_int = int(course_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_course_id")

    try:
        return upsert_tracking(colleague_id, course_id_int, status)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_status")


@router.post("/delete", response_model=dict)
def delete_tracking(payload: dict, current_user: str = Depends(require_session)):
    """Remove tracking status for a course.

    Args:
        payload: Delete payload with course_id.
        current_user: Authenticated username.

    Returns:
        dict: Delete result.
    """
    colleague_id = current_user
    course_id = payload.get("course_id")

    if not course_id:
        raise HTTPException(status_code=400, detail="missing_fields")

    try:
        course_id_int = int(course_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_course_id")

    removed = remove_tracking(colleague_id, course_id_int)
    return {"removed": removed}


@router.get("/stats", response_model=dict)
def get_stats(
    colleague_id: Optional[str] = Query(default=None),
    current_user: str = Depends(require_session),
):
    """Return tracking stats for a colleague or team totals.

    Args:
        colleague_id: Optional colleague username to query.
        current_user: Authenticated username.

    Returns:
        dict: Stats payload.
    """
    if colleague_id and colleague_id != current_user and not auth_service.is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")
    if colleague_id:
        return stats_for_colleague(colleague_id)
    if auth_service.is_admin(current_user):
        return stats_all()
    raise HTTPException(status_code=403, detail="admin_required")


@router.get("/stats/users", response_model=list[dict])
def get_stats_by_user(current_user: str = Depends(require_session)):
    """Return tracking stats grouped by user (admin only).

    Args:
        current_user: Authenticated username.

    Returns:
        list[dict]: Stats by user.
    """
    if not auth_service.is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")
    return stats_by_user()


@router.get("/recent", response_model=list[dict])
def get_recent_activity(
    limit: int = Query(default=10),
    current_user: str = Depends(require_session),
):
    """Return recent activity for the team (admin only).

    Args:
        limit: Max number of records.
        current_user: Authenticated username.

    Returns:
        list[dict]: Recent activity records.
    """
    if not auth_service.is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")
    return list_recent_activity(limit=limit)
