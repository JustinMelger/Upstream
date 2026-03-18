"""Learning page orchestration for the NiceGUI frontend."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient, ApiError
from frontend.ui.nicegui.services._indexing import index_by_int_id
from frontend.ui.nicegui.services.courses_service import index_tracking_by_course_id


logger = logging.getLogger(__name__)


async def _load_summary_map(
    *,
    api: ApiClient,
    path: str,
    param_key: str,
    ids: list[int],
    row_id_key: str,
    log_context: str,
) -> dict[int, dict[str, Any]]:
    """Best-effort summary loader with typed fallback logging."""
    out: dict[int, dict[str, Any]] = {}
    if not ids:
        return out
    try:
        rows = await api.get(path, params={param_key: ids})
    except ApiError as exc:
        logger.warning(
            "Learning summary unavailable",
            extra={
                "context": log_context,
                "status_code": int(exc.status_code),
                "id_count": len(ids),
                "endpoint": path,
            },
        )
        return out
    for row in list(rows or []):
        if not isinstance(row, dict):
            continue
        try:
            row_id = int(row.get(row_id_key) or 0)
        except (TypeError, ValueError):
            continue
        if row_id > 0:
            out[row_id] = row
    return out


async def set_tracking_status(*, api: ApiClient, course_id: int, status: str) -> None:
    """Set tracking status for a course."""
    await api.post("/tracking", {"course_id": int(course_id), "status": str(status)})


async def clear_tracking_status(*, api: ApiClient, course_id: int) -> None:
    """Clear tracking status for a course."""
    await api.post("/tracking/delete", {"course_id": int(course_id)})


async def save_recommended_course(*, api: ApiClient, course_id: int) -> None:
    """Save a recommended course as interested."""
    await set_tracking_status(api=api, course_id=int(course_id), status="interested")


async def save_recommended_path(*, api: ApiClient, path_id: int) -> None:
    """Save a recommended path as selected."""
    await api.post(f"/paths/{int(path_id)}/select", {})


def _int_id_list(rows: list[dict[str, Any]], *, key: str) -> list[int]:
    out: list[int] = []
    for row in rows:
        raw = row.get(key)
        if raw is None:
            continue
        try:
            value = int(raw)
        except (TypeError, ValueError):
            continue
        if value > 0:
            out.append(value)
    return out


async def _load_selected_path_details(*, api: ApiClient, selected_ids: list[int]) -> dict[int, dict[str, Any]]:
    if not selected_ids:
        return {}
    detail_results = await asyncio.gather(*(api.get(f"/paths/{pid}") for pid in selected_ids), return_exceptions=True)
    ok_details: list[dict[str, Any]] = [payload for payload in detail_results if isinstance(payload, dict)]
    return index_by_int_id(ok_details, key="id")


async def _load_recommendation_summaries(
    *,
    api: ApiClient,
    courses: list[dict[str, Any]],
    paths: list[dict[str, Any]],
) -> tuple[dict[int, dict[str, Any]], dict[int, dict[str, Any]]]:
    all_course_ids = sorted(int(c.get("id") or 0) for c in courses if isinstance(c, dict) and int(c.get("id") or 0) > 0)
    all_path_ids = sorted(int(p.get("id") or 0) for p in paths if isinstance(p, dict) and int(p.get("id") or 0) > 0)
    course_map = await _load_summary_map(
        api=api,
        path="/courses/recommendations/summary",
        param_key="course_ids",
        ids=all_course_ids,
        row_id_key="course_id",
        log_context="all_course_recommendations",
    )
    path_map = await _load_summary_map(
        api=api,
        path="/paths/recommendations/summary",
        param_key="path_ids",
        ids=all_path_ids,
        row_id_key="path_id",
        log_context="all_path_recommendations",
    )
    return course_map, path_map


async def _pending_review_ids(
    *,
    api: ApiClient,
    ids: list[int],
    username: str,
    endpoint_builder: Any,
) -> list[int]:
    if not ids:
        return []
    review_rows = await asyncio.gather(*(api.get(endpoint_builder(int(item_id))) for item_id in ids), return_exceptions=True)
    pending: list[int] = []
    for item_id, rows in zip(ids, review_rows, strict=False):
        if isinstance(rows, Exception) or not isinstance(rows, list):
            continue
        mine = any(isinstance(row, dict) and str(row.get("created_by") or "") == username for row in rows)
        if not mine:
            pending.append(int(item_id))
    return pending


def _recommended_courses_for_user(
    *,
    courses: list[dict[str, Any]],
    tracking_by_course_id: dict[int, dict[str, Any]],
    username: str,
    recommendation_summary_by_id: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for course in courses:
        cid = int(course.get("id") or 0)
        if cid <= 0 or cid in tracking_by_course_id or str(course.get("created_by") or "") == username:
            continue
        count = int((recommendation_summary_by_id.get(cid) or {}).get("recommendation_count") or 0)
        if count <= 0:
            continue
        out.append(
            {"course_id": cid, "course": course, "recommendation_count": count, "why": f"{count} teammate recommendation(s)"}
        )
    return sorted(
        out,
        key=lambda row: (int(row.get("recommendation_count") or 0), int(row.get("course_id") or 0)),
        reverse=True,
    )[:5]


def _recommended_paths_for_user(
    *,
    paths: list[dict[str, Any]],
    selected_ids: list[int],
    username: str,
    recommendation_summary_by_id: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    selected_set = {int(pid) for pid in selected_ids}
    for path in paths:
        pid = int(path.get("id") or 0)
        if pid <= 0 or pid in selected_set or str(path.get("created_by") or "") == username:
            continue
        count = int((recommendation_summary_by_id.get(pid) or {}).get("recommendation_count") or 0)
        if count <= 0:
            continue
        out.append({"path_id": pid, "path": path, "recommendation_count": count, "why": f"{count} teammate recommendation(s)"})
    return sorted(
        out,
        key=lambda row: (int(row.get("recommendation_count") or 0), int(row.get("path_id") or 0)),
        reverse=True,
    )[:5]


async def _load_shared_summaries(
    *,
    api: ApiClient,
    shared_course_ids: list[int],
    shared_video_ids: list[int],
    shared_path_ids: list[int],
) -> tuple[
    dict[int, dict[str, Any]],
    dict[int, dict[str, Any]],
    dict[int, dict[str, Any]],
    dict[int, dict[str, Any]],
    dict[int, dict[str, Any]],
]:
    shared_course_reviews = await _load_summary_map(
        api=api,
        path="/courses/reviews/summary",
        param_key="course_ids",
        ids=shared_course_ids,
        row_id_key="course_id",
        log_context="shared_course_reviews",
    )
    shared_course_recommendations = await _load_summary_map(
        api=api,
        path="/courses/recommendations/summary",
        param_key="course_ids",
        ids=shared_course_ids,
        row_id_key="course_id",
        log_context="shared_course_recommendations",
    )
    shared_video_reviews = await _load_summary_map(
        api=api,
        path="/videos/reviews/summary",
        param_key="video_ids",
        ids=shared_video_ids,
        row_id_key="video_id",
        log_context="shared_video_reviews",
    )
    shared_path_reviews = await _load_summary_map(
        api=api,
        path="/paths/reviews/summary",
        param_key="path_ids",
        ids=shared_path_ids,
        row_id_key="path_id",
        log_context="shared_path_reviews",
    )
    shared_path_recommendations = await _load_summary_map(
        api=api,
        path="/paths/recommendations/summary",
        param_key="path_ids",
        ids=shared_path_ids,
        row_id_key="path_id",
        log_context="shared_path_recommendations",
    )
    return (
        shared_course_reviews,
        shared_course_recommendations,
        shared_video_reviews,
        shared_path_reviews,
        shared_path_recommendations,
    )


def _build_learning_collections(
    *,
    courses: list[dict[str, Any]],
    videos: list[dict[str, Any]],
    paths: list[dict[str, Any]],
    articles: list[dict[str, Any]],
    tracking_by_course_id: dict[int, dict[str, Any]],
    selected_ids: list[int],
    username: str,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[int],
    list[int],
    list[int],
    list[int],
]:
    shared_courses = [c for c in courses if str(c.get("created_by") or "") == username]
    shared_videos = [v for v in videos if str(v.get("created_by") or "") == username]
    shared_paths = [p for p in paths if str(p.get("created_by") or "") == username]
    shared_articles = [a for a in articles if str(a.get("created_by") or "") == username]

    tracked_course_ids = {int(cid) for cid in tracking_by_course_id.keys()}
    tracked_courses = [c for c in courses if int(c.get("id") or 0) in tracked_course_ids]

    tracked_ids_sorted = sorted(int(c.get("id") or 0) for c in tracked_courses if int(c.get("id") or 0) > 0)
    selected_ids_sorted = sorted(int(pid) for pid in selected_ids if int(pid) > 0)
    shared_course_ids = sorted(int(c.get("id") or 0) for c in shared_courses if int(c.get("id") or 0) > 0)
    shared_video_ids = sorted(int(v.get("id") or 0) for v in shared_videos if int(v.get("id") or 0) > 0)
    shared_path_ids = sorted(int(p.get("id") or 0) for p in shared_paths if int(p.get("id") or 0) > 0)
    return (
        shared_courses,
        shared_videos,
        shared_paths,
        shared_articles,
        tracked_courses,
        tracked_ids_sorted,
        selected_ids_sorted,
        shared_course_ids,
        shared_video_ids,
        shared_path_ids,
    )


async def load_my_learning_data(
    *,
    api: ApiClient,
    username: str,
    include_articles: bool,
) -> dict[str, Any]:
    """Load data for the My learning page.

    Notes:
        This currently loads full lists and filters client-side. It is fine for
        small/medium catalogs and keeps the backend API simple.

    Args:
        api: API client.
        username: Current username.
        include_articles: Whether to load articles.

    Returns:
        Dict containing learning + shared datasets for rendering.
    """
    courses_task = api.get("/courses")
    tracking_task = api.get("/tracking")
    selected_paths_task = api.get("/paths/selected/list")
    paths_task = api.get("/paths")
    videos_task = api.get("/videos")
    articles_task = api.get("/articles") if include_articles else asyncio.sleep(0, result=[])

    courses_result, tracking_result, selected_paths_result, paths_result, videos_result, articles_result = await asyncio.gather(
        courses_task, tracking_task, selected_paths_task, paths_task, videos_task, articles_task
    )

    courses = list(courses_result or [])
    tracking_rows = list(tracking_result or [])
    tracking_by_course_id = index_tracking_by_course_id(tracking_rows)

    selected_paths = list(selected_paths_result or [])
    selected_ids = _int_id_list(selected_paths, key="id")
    path_details_by_id = await _load_selected_path_details(api=api, selected_ids=selected_ids)

    paths = list(paths_result or [])
    videos = list(videos_result or [])
    articles = list(articles_result or [])
    (
        shared_courses,
        shared_videos,
        shared_paths,
        shared_articles,
        tracked_courses,
        tracked_ids_sorted,
        selected_ids_sorted,
        shared_course_ids,
        shared_video_ids,
        shared_path_ids,
    ) = _build_learning_collections(
        courses=courses,
        videos=videos,
        paths=paths,
        articles=articles,
        tracking_by_course_id=tracking_by_course_id,
        selected_ids=selected_ids,
        username=username,
    )

    course_review_summary_by_id = await _load_summary_map(
        api=api,
        path="/courses/reviews/summary",
        param_key="course_ids",
        ids=tracked_ids_sorted,
        row_id_key="course_id",
        log_context="tracked_course_reviews",
    )

    path_review_summary_by_id = await _load_summary_map(
        api=api,
        path="/paths/reviews/summary",
        param_key="path_ids",
        ids=selected_ids_sorted,
        row_id_key="path_id",
        log_context="selected_path_reviews",
    )

    course_recommendation_summary_by_id, path_recommendation_summary_by_id = await _load_recommendation_summaries(
        api=api,
        courses=courses,
        paths=paths,
    )

    pending_course_review_ids = await _pending_review_ids(
        api=api,
        ids=tracked_ids_sorted,
        username=username,
        endpoint_builder=lambda cid: f"/courses/{int(cid)}/reviews",
    )
    pending_path_review_ids = await _pending_review_ids(
        api=api,
        ids=selected_ids_sorted,
        username=username,
        endpoint_builder=lambda pid: f"/paths/{int(pid)}/reviews",
    )

    recommended_courses_for_you = _recommended_courses_for_user(
        courses=courses,
        tracking_by_course_id=tracking_by_course_id,
        username=username,
        recommendation_summary_by_id=course_recommendation_summary_by_id,
    )
    recommended_paths_for_you = _recommended_paths_for_user(
        paths=paths,
        selected_ids=selected_ids_sorted,
        username=username,
        recommendation_summary_by_id=path_recommendation_summary_by_id,
    )

    (
        shared_course_review_summary_by_id,
        shared_course_recommendation_summary_by_id,
        shared_video_review_summary_by_id,
        shared_path_review_summary_by_id,
        shared_path_recommendation_summary_by_id,
    ) = await _load_shared_summaries(
        api=api,
        shared_course_ids=shared_course_ids,
        shared_video_ids=shared_video_ids,
        shared_path_ids=shared_path_ids,
    )

    return {
        "courses": courses,
        "tracking_by_course_id": tracking_by_course_id,
        "tracked_courses": tracked_courses,
        "selected_paths": selected_paths,
        "path_details_by_id": path_details_by_id,
        "paths": paths,
        "shared_courses": shared_courses,
        "videos": videos,
        "shared_videos": shared_videos,
        "shared_paths": shared_paths,
        "articles": articles,
        "shared_articles": shared_articles,
        "course_review_summary_by_id": course_review_summary_by_id,
        "path_review_summary_by_id": path_review_summary_by_id,
        "course_recommendation_summary_by_id": course_recommendation_summary_by_id,
        "path_recommendation_summary_by_id": path_recommendation_summary_by_id,
        "pending_course_review_ids": pending_course_review_ids,
        "pending_path_review_ids": pending_path_review_ids,
        "recommended_courses_for_you": recommended_courses_for_you,
        "recommended_paths_for_you": recommended_paths_for_you,
        "shared_course_review_summary_by_id": shared_course_review_summary_by_id,
        "shared_course_recommendation_summary_by_id": shared_course_recommendation_summary_by_id,
        "shared_video_review_summary_by_id": shared_video_review_summary_by_id,
        "shared_path_review_summary_by_id": shared_path_review_summary_by_id,
        "shared_path_recommendation_summary_by_id": shared_path_recommendation_summary_by_id,
    }
