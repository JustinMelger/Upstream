"""Pure typed view-model helpers for Explore list rendering."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from frontend.ui.nicegui.core.datetime_utils import parse_iso_datetime
from frontend.ui.nicegui.core.learning_items import (
    infer_learning_item_type,
    interleave_learning_item_entries,
)
from frontend.ui.nicegui.pages.articles.reducers import derive_shown_articles
from frontend.ui.nicegui.pages.courses.reducers import filter_courses, sort_courses
from frontend.ui.nicegui.pages.explore.state import ExplorePageState
from frontend.ui.nicegui.pages.explore.ui_glue import apply_tab_scope, compute_explore_meta_text
from frontend.ui.nicegui.pages.paths.reducers import filter_paths_by_needle, sort_paths


class ExploreListFilters(BaseModel):
    """Normalized Explore list filter values."""

    model_config = ConfigDict(frozen=True)

    tab: str = "all"
    sort: str = ""
    needle: str = ""
    provider: str = ""
    category: str = ""
    tag: str = ""
    author: str = ""


class ExploreVisibleResults(BaseModel):
    """Computed Explore results visible for the current filters."""

    model_config = ConfigDict(frozen=True)

    shown_courses: list[dict[str, Any]] = Field(default_factory=list)
    shown_videos: list[dict[str, Any]] = Field(default_factory=list)
    shown_paths: list[dict[str, Any]] = Field(default_factory=list)
    shown_articles: list[dict[str, Any]] = Field(default_factory=list)
    shown_learning_items: list["ExploreLearningItemEntry"] = Field(default_factory=list)
    meta_text: str = ""


class ExploreLearningItemEntry(BaseModel):
    """Typed mixed-feed entry used by Explore learning-item rendering."""

    model_config = ConfigDict(frozen=True)

    learning_item_type: str
    id: int
    row: dict[str, Any]


def _build_learning_item_entries(
    *,
    courses: list[dict[str, Any]],
    videos: list[dict[str, Any]],
    articles: list[dict[str, Any]],
) -> list[ExploreLearningItemEntry]:
    """Build a unified Explore learning-item list with explicit type signaling."""
    entries: list[ExploreLearningItemEntry] = []
    for row in list(courses or []):
        entries.append(
            ExploreLearningItemEntry(
                learning_item_type=infer_learning_item_type(
                    url=str(row.get("url") or ""),
                    provider=str(row.get("provider") or ""),
                    fallback="course",
                ),
                id=int(row.get("id") or 0),
                row=row,
            )
        )
    for row in list(videos or []):
        entries.append(
            ExploreLearningItemEntry(
                learning_item_type="video",
                id=int(row.get("id") or 0),
                row=row,
            )
        )
    for row in list(articles or []):
        entries.append(
            ExploreLearningItemEntry(
                learning_item_type="article",
                id=int(row.get("id") or 0),
                row=row,
            )
        )
    return interleave_learning_item_entries(entries=entries)


def _filter_and_sort_videos(
    *,
    videos: list[dict[str, Any]],
    needle: str,
    provider: str,
    category: str,
    sort: str,
) -> list[dict[str, Any]]:
    normalized_needle = str(needle or "").strip().lower()
    normalized_provider = str(provider or "").strip().lower()
    normalized_category = str(category or "").strip().lower()
    rows: list[dict[str, Any]] = []
    for row in list(videos or []):
        if normalized_provider and str(row.get("provider") or "").strip().lower() != normalized_provider:
            continue
        if normalized_category and str(row.get("category") or "").strip().lower() != normalized_category:
            continue
        if normalized_needle:
            haystack = " ".join(
                [
                    str(row.get("title") or ""),
                    str(row.get("description") or ""),
                    str(row.get("provider") or ""),
                    str(row.get("category") or ""),
                    str(row.get("url") or ""),
                ]
            ).lower()
            if normalized_needle not in haystack:
                continue
        rows.append(row)
    sort_value = str(sort or "")
    if sort_value == "title_az":
        return sorted(rows, key=lambda row: str(row.get("title") or "").lower())
    if sort_value == "newest":
        return sorted(rows, key=lambda row: str(row.get("created_at") or ""), reverse=True)
    return sorted(rows, key=lambda row: str(row.get("title") or "").lower())


def build_explore_visible_results(*, state: ExplorePageState, filters: ExploreListFilters) -> ExploreVisibleResults:
    """Compute visible Explore datasets and topbar meta text for current controls."""
    shown_courses = filter_courses(
        courses=list(state.courses or []),
        tracking_by_course_id=dict(state.tracking_by_course_id or {}),
        scope_value="all",
        needle=str(filters.needle or ""),
        provider_value=str(filters.provider or ""),
        category_value=str(filters.category or ""),
        level_value="",
        status_value="",
    )
    shown_courses = sort_courses(
        courses=shown_courses,
        sort_value=str(filters.sort or ""),
        review_summary_by_course_id=dict(state.course_review_summary_by_course_id or {}),
        parse_iso_datetime=parse_iso_datetime,
    )

    shown_articles = derive_shown_articles(
        articles=list(state.articles or []),
        needle=str(filters.needle or ""),
        tag_value=str(filters.tag or ""),
        author_value=str(filters.author or ""),
        sort_value=str(filters.sort or ""),
    )
    shown_videos = _filter_and_sort_videos(
        videos=list(state.videos or []),
        needle=str(filters.needle or ""),
        provider=str(filters.provider or ""),
        category=str(filters.category or ""),
        sort=str(filters.sort or ""),
    )
    shown_paths = filter_paths_by_needle(list(state.paths or []), str(filters.needle or "").lower())
    shown_paths = sort_paths(
        paths=shown_paths,
        sort_value=str(filters.sort or ""),
        path_review_summary_by_id=dict(state.path_review_summary_by_id or {}),
        parse_iso_datetime=parse_iso_datetime,
    )

    shown_courses, shown_videos, shown_paths, shown_articles = apply_tab_scope(
        tab_value=str(filters.tab or "all"),
        shown_courses=shown_courses,
        shown_videos=shown_videos,
        shown_paths=shown_paths,
        shown_articles=shown_articles,
    )
    return ExploreVisibleResults(
        shown_courses=shown_courses,
        shown_videos=shown_videos,
        shown_paths=shown_paths,
        shown_articles=shown_articles,
        shown_learning_items=_build_learning_item_entries(courses=shown_courses, videos=shown_videos, articles=shown_articles),
        meta_text=compute_explore_meta_text(
            tab_value=str(filters.tab or "all"),
            course_count=len(shown_courses),
            video_count=len(shown_videos),
            path_count=len(shown_paths),
            article_count=len(shown_articles),
        ),
    )
