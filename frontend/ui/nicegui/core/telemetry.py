"""Frontend telemetry helpers."""

from __future__ import annotations

import asyncio
from datetime import datetime, UTC
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.core.config import settings


def _event_payload(*, event_name: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "event_name": str(event_name or "").strip(),
        "context": dict(context or {}),
        "happened_at": datetime.now(UTC).isoformat(),
    }


def track_ui_event_nowait(*, api: ApiClient, event_name: str, context: dict[str, Any] | None = None) -> None:
    """Fire-and-forget telemetry emit; ignore failures in UI flows."""
    if not settings.feature_telemetry:
        return
    post = getattr(api, "post", None)
    if not callable(post):
        return

    async def _send() -> None:
        try:
            await post("/telemetry/events", _event_payload(event_name=event_name, context=context))
        except ApiError:
            return

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    loop.create_task(_send())
