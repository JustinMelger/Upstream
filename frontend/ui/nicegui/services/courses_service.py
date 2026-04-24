"""Courses-related orchestration for the NiceGUI frontend."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import time
from typing import Any, Sequence

from frontend.ui.nicegui.core.api_client import ApiClient


def index_tracking_by_course_id(rows: Sequence[object] | None) -> dict[int, dict[str, Any]]:
    """Index tracking rows by integer `course_id`."""
    out: dict[int, dict[str, Any]] = {}
    for r in list(rows or []):
        if not isinstance(r, dict):
            continue
        raw = str(r.get("course_id") or "")
        if not raw.isdigit():
            continue
        out[int(raw)] = r
    return out


@dataclass(slots=True)
class CourseDetailBundle:
    """Cached payloads used by course detail dialog rendering."""

    course: dict[str, Any]
    reviews: list[dict[str, Any]]


_COURSE_DETAIL_CACHE: dict[tuple[str, int], tuple[float, CourseDetailBundle]] = {}
_COURSE_DETAIL_CACHE_TTL_SECONDS = 20.0


def clear_course_detail_cache(*, course_id: int | None = None, cache_scope: str = "") -> None:
    """Clear cached course detail payloads."""
    if course_id is None:
        if str(cache_scope or ""):
            scope = str(cache_scope or "")
            keys = [key for key in _COURSE_DETAIL_CACHE.keys() if key[0] == scope]
            for key in keys:
                _COURSE_DETAIL_CACHE.pop(key, None)
        else:
            _COURSE_DETAIL_CACHE.clear()
        return
    _COURSE_DETAIL_CACHE.pop((str(cache_scope or ""), int(course_id)), None)


async def load_course_detail_bundle(
    *,
    api: ApiClient,
    course_id: int,
    cache_scope: str = "",
    now_fn: Any = time.monotonic,
    ttl_seconds: float = _COURSE_DETAIL_CACHE_TTL_SECONDS,
) -> CourseDetailBundle:
    """Load detail dialog payloads with short-TTL caching."""
    cid = int(course_id)
    scope = str(cache_scope or "")
    cache_key = (scope, cid)
    now = float(now_fn())
    cached = _COURSE_DETAIL_CACHE.get(cache_key)
    if isinstance(cached, tuple) and len(cached) == 2:
        expiry, payload = cached
        if float(expiry) > now:
            return payload

    course, reviews_payload = await asyncio.gather(
        api.get(f"/courses/{cid}"),
        api.get(f"/courses/{cid}/reviews"),
    )
    bundle = CourseDetailBundle(
        course=dict(course or {}),
        reviews=list(reviews_payload or []),
    )
    _COURSE_DETAIL_CACHE[cache_key] = (now + float(ttl_seconds), bundle)
    return bundle


async def load_courses_and_tracking(
    *,
    api: ApiClient,
    course_params: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]]]:
    """Load courses and the user's tracking map in one shot."""
    courses_result, tracking_result = await asyncio.gather(
        api.get("/courses", params=course_params or None),
        api.get("/tracking"),
    )
    courses = list(courses_result or [])
    tracking_by_course_id = index_tracking_by_course_id(list(tracking_result or []))
    return courses, tracking_by_course_id


async def load_tracking_map(*, api: ApiClient) -> dict[int, dict[str, Any]]:
    """Load only tracking rows and index them by course id."""
    tracking_result = await api.get("/tracking")
    return index_tracking_by_course_id(list(tracking_result or []))


async def load_review_summaries(*, api: ApiClient, course_ids: list[int]) -> dict[int, dict[str, Any]]:
    """Load review summary items for the given course ids and index them by course id."""
    if not course_ids:
        return {}
    result = await api.get("/courses/reviews/summary", params={"course_ids": [int(i) for i in course_ids if int(i) > 0]})
    out: dict[int, dict[str, Any]] = {}
    for row in list(result or []):
        try:
            cid = int(row.get("course_id") or 0)
        except (TypeError, ValueError):
            continue
        if cid <= 0:
            continue
        out[cid] = row
    return out

