from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import require_session
from backend.services.auth_service import is_admin
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
    target = colleague_id or current_user
    if target != current_user and not is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")
    return list_tracking(colleague_id=target)


@router.post("", response_model=dict)
def set_tracking(payload: dict, current_user: str = Depends(require_session)):
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
    if colleague_id and colleague_id != current_user and not is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")
    if colleague_id:
        return stats_for_colleague(colleague_id)
    if is_admin(current_user):
        return stats_all()
    raise HTTPException(status_code=403, detail="admin_required")


@router.get("/stats/users", response_model=list[dict])
def get_stats_by_user(current_user: str = Depends(require_session)):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")
    return stats_by_user()


@router.get("/recent", response_model=list[dict])
def get_recent_activity(
    limit: int = Query(default=10),
    current_user: str = Depends(require_session),
):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")
    return list_recent_activity(limit=limit)
