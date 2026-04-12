from typing import Any

from fastapi import APIRouter, Depends, Query

from backend.api.deps import get_notifications_service, require_session
from backend.api.schemas.notifications import NotificationActivityItem
from backend.services.notifications_service import NotificationsService


router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/activity", response_model=list[NotificationActivityItem])
async def list_activity_notifications(
    limit: int = Query(default=30, ge=1, le=100),
    scope: str = Query(default="inbox", pattern="^(inbox|team)$"),
    current_user: str = Depends(require_session),
    notifications: NotificationsService = Depends(get_notifications_service),
) -> list[dict[str, Any]]:
    """Return a lightweight activity feed for shared and rated content."""
    return await notifications.list_activity(current_user=current_user, limit=int(limit), scope=str(scope))
