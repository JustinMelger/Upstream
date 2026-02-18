from __future__ import annotations

from pydantic import StrictInt, StrictStr

from backend.api.schemas.common import APIModel


class NotificationActivityItem(APIModel):
    """Activity feed item payload."""

    event_id: StrictStr
    event_type: StrictStr
    created_at: StrictStr
    actor: StrictStr
    message: StrictStr
    target_type: StrictStr
    target_id: StrictInt
    target_label: StrictStr
