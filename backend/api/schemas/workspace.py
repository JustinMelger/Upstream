"""Public typed contracts for the React read models."""

from __future__ import annotations

from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field


ContentType = Literal["course", "article", "video", "path"]
T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    """A bounded server-filtered page."""

    items: list[T]
    total: int
    page: int
    page_size: int


class CatalogItem(BaseModel):
    """Common display fields; subtype capabilities remain explicit."""

    type: ContentType
    id: int
    title: str
    description: str | None = None
    provider: str = ""
    category: str = ""
    level: str = ""
    duration_hours: float | None = None
    url: str | None = None
    created_by: str | None = None
    created_at: datetime | None = None
    recommendation_note: str | None = None
    rating: float = 0
    review_count: int = 0
    status: str | None = None


class NextCourse(BaseModel):
    """The next actionable course and current-user status."""

    id: int
    title: str
    url: str | None = None
    provider: str | None = None
    duration_hours: float | None = None
    status: str | None = None


class CourseCompletion(BaseModel):
    """Personal course totals within a selected path."""

    completed: int
    total: int


class LearningItem(CatalogItem):
    """A personal collection item; progress is never part of catalog responses."""

    course_progress: CourseCompletion | None = None


class LearningSummary(BaseModel):
    """Current personal counts, not historical trend estimates."""

    interested: int
    in_progress: int
    completed: int
    selected_paths: int
    contributions: int
    next_course: NextCourse | None = None


class CourseProgress(BaseModel):
    """A course's status in a mixed path."""

    id: int
    status: str | None = None


class PathProgress(BaseModel):
    """Selection state is independent of course completion."""

    selected: bool
    status: str | None = None
    courses: list[CourseProgress]
    completed: int
    total: int


class ActivityEvent(BaseModel):
    """A share or review of globally visible content."""

    event_id: str
    event_type: Literal["share", "review"]
    type: ContentType
    content_id: int
    title: str
    actor: str
    happened_at: datetime
    rating: float | None = None
    excerpt: str | None = Field(default=None, max_length=280)
    excerpt_kind: Literal["recommendation", "description", "review"] | None = None


class CatalogFilters(BaseModel):
    """Validate bounded catalog queries."""

    q: str = Field(default="", max_length=200)
    type: ContentType | None = None
    provider: str = ""
    category: str = ""
    author: str = ""
    sort: Literal["newest", "title", "rating"] = "newest"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=24, ge=1, le=100)


class LearningFilters(BaseModel):
    """Validate personal collection queries."""

    view: Literal["tracked", "paths", "contributions"] = "tracked"
    status: Literal["interested", "in_progress", "completed"] | None = None
    content_id: int | None = Field(default=None, ge=1)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=24, ge=1, le=100)


class FacetFilters(CatalogFilters):
    """Search bounded provider/category options within the active catalog filters."""

    field: Literal["provider", "category"]
    option_q: str = Field(default="", max_length=200)


class ActivityFilters(BaseModel):
    """Validate activity scope and paging."""

    scope: Literal["personal", "shared"] = "personal"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=24, ge=1, le=100)
