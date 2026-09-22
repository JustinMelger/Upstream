from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_tracking_service, require_session
from backend.api.schemas import (
    TrackingDeleteRequest,
    TrackingDeleteResponse,
    TrackingRecordPayload,
    TrackingUpsertRequest,
)
from backend.services.tracking_service import TrackingService


router = APIRouter(prefix="/tracking", tags=["tracking"])


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
