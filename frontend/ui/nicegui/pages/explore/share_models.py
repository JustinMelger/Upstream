"""Typed models for Explore share and URL helper flows."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ExploreSharePayload(BaseModel):
    """Generic share payload wrapper used by Explore mutation helpers."""

    model_config = ConfigDict(frozen=True)

    payload: dict[str, Any] = Field(default_factory=dict)


class ExploreUrlValue(BaseModel):
    """URL input wrapper used by Explore duplicate/suggest helpers."""

    model_config = ConfigDict(frozen=True)

    url: str = ""
