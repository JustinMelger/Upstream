from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    """Base Pydantic model for API schemas."""

    model_config = ConfigDict(extra="ignore", strict=True)


class ErrorResponse(APIModel):
    """Generic not-found style response payload."""

    error: str


class HealthResponse(APIModel):
    """Health check response payload."""

    status: str
