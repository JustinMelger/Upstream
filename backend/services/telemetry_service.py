from __future__ import annotations


"""Telemetry service for lightweight frontend event ingestion."""

import logging
from typing import Any

from opentelemetry import metrics, trace


logger = logging.getLogger(__name__)
_meter = metrics.get_meter(__name__)
_event_counter = _meter.create_counter(
    name="frontend_events_total",
    unit="1",
    description="Count of product telemetry events emitted by the frontend",
)

_tracer = trace.get_tracer(__name__)


class TelemetryService:
    """Accept and record low-risk product telemetry events."""

    def track_event(
        self,
        *,
        actor: str,
        event_name: str,
        context: dict[str, Any] | None = None,
        happened_at: str = "",
    ) -> None:
        """Record one telemetry event to structured logs."""
        name = str(event_name or "").strip() or "unknown"
        attributes = {"frontend.event.name": name}
        page = str((context or {}).get("page") or "").strip()
        if page:
            attributes["frontend.page"] = page

        if _event_counter is not None:
            _event_counter.add(1, attributes=attributes)
        if _tracer is not None:
            with _tracer.start_as_current_span("frontend.event") as span:
                span.set_attribute("frontend.event.name", name)
                if page:
                    span.set_attribute("frontend.page", page)
                span.set_attribute("enduser.id", str(actor or ""))
                span.add_event("frontend_event_ingested")

        logger.info(
            "telemetry_event actor=%s event=%s happened_at=%s context=%s",
            str(actor or ""),
            name,
            str(happened_at or ""),
            dict(context or {}),
        )
