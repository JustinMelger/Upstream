from __future__ import annotations


"""OpenTelemetry bootstrap for backend observability."""

from collections.abc import Iterable
import logging

from fastapi import FastAPI

from backend.core.config import settings


logger = logging.getLogger(__name__)
_INITIALIZED = False


def _parse_otlp_headers(raw: str) -> dict[str, str]:
    headers: dict[str, str] = {}
    for pair in (raw or "").split(","):
        if "=" not in pair:
            continue
        key, value = pair.split("=", 1)
        k = str(key).strip()
        v = str(value).strip()
        if k and v:
            headers[k] = v
    return headers


def _as_key_values(items: Iterable[tuple[str, str]]) -> dict[str, str]:
    return {str(k): str(v) for k, v in items}


def configure_observability(app: FastAPI) -> None:
    """Configure OpenTelemetry traces + metrics for the API process."""
    global _INITIALIZED
    if _INITIALIZED or not settings.otel_enabled:
        return

    try:
        from opentelemetry import metrics, trace
        from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.trace.sampling import ParentBased, TraceIdRatioBased
    except ImportError:
        logger.warning("OpenTelemetry packages are not installed; observability disabled at runtime")
        return

    resource = Resource.create(
        _as_key_values(
            [
                ("service.name", settings.otel_service_name),
                ("service.version", settings.otel_service_version),
                ("deployment.environment", settings.otel_deployment_environment),
            ]
        )
    )
    headers = _parse_otlp_headers(settings.otel_exporter_otlp_headers)

    trace_provider = TracerProvider(
        resource=resource,
        sampler=ParentBased(root=TraceIdRatioBased(rate=float(settings.otel_traces_sample_ratio))),
    )
    trace_provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(
                endpoint=settings.otel_exporter_otlp_traces_endpoint,
                headers=headers or None,
            )
        )
    )
    trace.set_tracer_provider(trace_provider)

    metric_reader = PeriodicExportingMetricReader(
        OTLPMetricExporter(
            endpoint=settings.otel_exporter_otlp_metrics_endpoint,
            headers=headers or None,
        ),
        export_interval_millis=max(5000, int(settings.otel_metrics_export_interval_ms)),
    )
    metrics.set_meter_provider(MeterProvider(resource=resource, metric_readers=[metric_reader]))

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
    SQLAlchemyInstrumentor().instrument()
    _INITIALIZED = True
    logger.info("OpenTelemetry initialized for service=%s", settings.otel_service_name)
