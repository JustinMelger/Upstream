from __future__ import annotations

from fastapi import APIRouter, Depends

from backend.api.deps import require_session
from backend.api.schemas import TelemetryEventRequest, TelemetryEventResponse
from backend.services.telemetry_service import TelemetryService


router = APIRouter(prefix="/telemetry", tags=["telemetry"])

_TELEMETRY = TelemetryService()


@router.post("/events", response_model=TelemetryEventResponse)
async def create_telemetry_event(
    payload: TelemetryEventRequest,
    current_user: str = Depends(require_session),
) -> TelemetryEventResponse:
    """Record one telemetry event emitted by the frontend."""
    _TELEMETRY.track_event(
        actor=str(current_user or ""),
        event_name=str(payload.event_name or "").strip(),
        context=dict(payload.context or {}),
        happened_at=str(payload.happened_at or ""),
    )
    return TelemetryEventResponse(accepted=True)
