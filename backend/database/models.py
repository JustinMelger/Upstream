from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UserRecord:
    """User row representation."""

    username: str
    password_hash: str
    role: str
    disabled: bool


@dataclass(frozen=True)
class SessionRecord:
    """Session row representation."""

    colleague_id: str
    expires_at: str


@dataclass(frozen=True)
class CourseRecord:
    """Course row representation."""

    id: int
    title: str
    provider: str | None
    category: str | None
    level: str | None
    duration_hours: float | None
    url: str | None
    created_at: str | None
