from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException, Query

from backend.services.auth_service import is_admin
from backend.services.tracking_service import list_tracking, stats_all, stats_for_colleague, upsert_tracking

router = APIRouter(prefix="/tracking", tags=["tracking"])


@router.get("", response_model=List[dict])
def get_tracking(colleague_id: Optional[str] = Query(default=None)):
    return list_tracking(colleague_id=colleague_id)


@router.post("", response_model=dict)
def set_tracking(payload: dict):
    colleague_id = (payload.get("colleague_id") or "").strip()
    course_id = payload.get("course_id")
    status = (payload.get("status") or "").strip()

    if not colleague_id or not course_id or not status:
        raise HTTPException(status_code=400, detail="missing_fields")

    try:
        course_id_int = int(course_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_course_id")

    try:
        return upsert_tracking(colleague_id, course_id_int, status)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_status")


@router.get("/stats", response_model=dict)
def get_stats(
    colleague_id: Optional[str] = Query(default=None),
    x_user_email: str | None = Header(default=None),
):
    if colleague_id:
        return stats_for_colleague(colleague_id)
    if is_admin(x_user_email):
        return stats_all()
    raise HTTPException(status_code=403, detail="admin_required")
