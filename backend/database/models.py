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
    description: str
    learning_outcomes: str | None
    prerequisites: str | None
    language: str | None
    provider: str | None
    category: str | None
    level: str | None
    duration_hours: float | None
    url: str | None
    created_at: str | None
    created_by: str | None


@dataclass(frozen=True)
class PathRecord:
    """Learning path row representation."""

    id: int
    name: str
    description: str | None
    created_by: str | None


@dataclass(frozen=True)
class PathCourseRecord:
    """Course row within a learning path (includes ordering position)."""

    id: int
    title: str
    provider: str | None
    category: str | None
    level: str | None
    duration_hours: float | None
    url: str | None
    position: int | None


@dataclass(frozen=True)
class SelectedPathRecord:
    """A learning path selected by a user (includes status)."""

    id: int
    name: str
    description: str | None
    status: str | None


@dataclass(frozen=True)
class TrackingRecord:
    """Course tracking row representation."""

    colleague_id: str
    course_id: int
    status: str
    updated_at: str


@dataclass(frozen=True)
class ArticleRecord:
    """Shared article/link row representation."""

    id: int
    title: str
    url: str
    tags: str | None
    created_by: str
    created_at: str


@dataclass(frozen=True)
class CourseReviewRecord:
    """Course review row representation."""

    id: int
    course_id: int
    rating: int
    text: str | None
    created_by: str
    created_at: str


@dataclass(frozen=True)
class PathReviewRecord:
    """Path review row representation."""

    id: int
    path_id: int
    rating: int
    text: str | None
    created_by: str
    created_at: str


@dataclass(frozen=True)
class ArticleReviewRecord:
    """Article review row representation."""

    id: int
    article_id: int
    rating: int
    text: str | None
    created_by: str
    created_at: str


@dataclass(frozen=True)
class CourseRecommendationRecord:
    """Course recommendation row representation."""

    id: int
    course_id: int
    note: str | None
    created_by: str
    created_at: str


@dataclass(frozen=True)
class PathRecommendationRecord:
    """Path recommendation row representation."""

    id: int
    path_id: int
    note: str | None
    created_by: str
    created_at: str


@dataclass(frozen=True)
class TeamRecord:
    """Team row representation."""

    id: int
    name: str
    description: str | None
    owner_user_id: str
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class TeamMemberRecord:
    """Team membership row representation."""

    team_id: int
    user_id: str
    role: str
    created_at: str
    updated_at: str
