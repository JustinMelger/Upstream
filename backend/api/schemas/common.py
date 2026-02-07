from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class APIModel(BaseModel):
    """Base Pydantic model for API schemas."""

    model_config = ConfigDict(extra="ignore", strict=True)


class ErrorResponse(APIModel):
    error: str


class HealthResponse(APIModel):
    status: str
