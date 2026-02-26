from __future__ import annotations

from typing import Any

from backend.api.schemas.common import APIModel


class TelemetryEventRequest(APIModel):
    """Request payload for frontend telemetry events."""

    event_name: str
    context: dict[str, Any] = {}
    happened_at: str = ""


class TelemetryEventResponse(APIModel):
    """Response payload for telemetry ingestion."""

    accepted: bool
