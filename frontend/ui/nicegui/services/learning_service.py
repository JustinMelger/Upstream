"""Learning page orchestration for the NiceGUI frontend."""

from __future__ import annotations

import asyncio
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.services._indexing import index_by_int_id
from frontend.ui.nicegui.services.courses_service import index_tracking_by_course_id


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
    articles_task = api.get("/articles") if include_articles else asyncio.sleep(0, result=[])

    courses_result, tracking_result, selected_paths_result, paths_result, articles_result = await asyncio.gather(
        courses_task, tracking_task, selected_paths_task, paths_task, articles_task
    )

    courses = list(courses_result or [])
    tracking_rows = list(tracking_result or [])
    tracking_by_course_id = index_tracking_by_course_id(tracking_rows)

    selected_paths = list(selected_paths_result or [])
    selected_ids: list[int] = []
    for row in selected_paths:
        if not isinstance(row, dict):
            continue
        raw = row.get("id")
        if raw is None:
            continue
        try:
            selected_ids.append(int(raw))
        except (TypeError, ValueError):
            continue

    path_details_by_id: dict[int, dict[str, Any]] = {}
    if selected_ids:
        detail_results = await asyncio.gather(*(api.get(f"/paths/{pid}") for pid in selected_ids), return_exceptions=True)
        ok_details: list[dict[str, Any]] = []
        for payload in detail_results:
            if isinstance(payload, Exception):
                continue
            if isinstance(payload, dict):
                ok_details.append(payload)
        path_details_by_id = index_by_int_id(ok_details, key="id")

    paths = list(paths_result or [])
    articles = list(articles_result or [])

    shared_courses = [c for c in courses if str(c.get("created_by") or "") == username]
    shared_paths = [p for p in paths if str(p.get("created_by") or "") == username]
    shared_articles = [a for a in articles if str(a.get("created_by") or "") == username]

    tracked_course_ids = {int(cid) for cid in tracking_by_course_id.keys()}
    tracked_courses = [c for c in courses if int(c.get("id") or 0) in tracked_course_ids]

    tracked_ids_sorted = sorted(int(c.get("id") or 0) for c in tracked_courses if int(c.get("id") or 0) > 0)
    selected_ids_sorted = sorted(int(pid) for pid in selected_ids if int(pid) > 0)

    course_review_summary_by_id: dict[int, dict[str, Any]] = {}
    if tracked_ids_sorted:
        try:
            rows = await api.get("/courses/reviews/summary", params={"course_ids": tracked_ids_sorted})
            for r in list(rows or []):
                if not isinstance(r, dict):
                    continue
                try:
                    cid = int(r.get("course_id") or 0)
                except (TypeError, ValueError):
                    continue
                if cid > 0:
                    course_review_summary_by_id[cid] = r
        except Exception:
            course_review_summary_by_id = {}

    path_review_summary_by_id: dict[int, dict[str, Any]] = {}
    if selected_ids_sorted:
        try:
            rows = await api.get("/paths/reviews/summary", params={"path_ids": selected_ids_sorted})
            for r in list(rows or []):
                if not isinstance(r, dict):
                    continue
                try:
                    pid = int(r.get("path_id") or 0)
                except (TypeError, ValueError):
                    continue
                if pid > 0:
                    path_review_summary_by_id[pid] = r
        except Exception:
            path_review_summary_by_id = {}

    pending_course_review_ids: list[int] = []
    if tracked_ids_sorted:
        course_review_rows = await asyncio.gather(
            *(api.get(f"/courses/{cid}/reviews") for cid in tracked_ids_sorted), return_exceptions=True
        )
        for cid, rows in zip(tracked_ids_sorted, course_review_rows, strict=False):
            if isinstance(rows, Exception):
                continue
            mine = False
            for row in list(rows or []):
                if not isinstance(row, dict):
                    continue
                if str(row.get("created_by") or "") == username:
                    mine = True
                    break
            if not mine:
                pending_course_review_ids.append(int(cid))

    pending_path_review_ids: list[int] = []
    if selected_ids_sorted:
        path_review_rows = await asyncio.gather(
            *(api.get(f"/paths/{pid}/reviews") for pid in selected_ids_sorted), return_exceptions=True
        )
        for pid, rows in zip(selected_ids_sorted, path_review_rows, strict=False):
            if isinstance(rows, Exception):
                continue
            mine = False
            for row in list(rows or []):
                if not isinstance(row, dict):
                    continue
                if str(row.get("created_by") or "") == username:
                    mine = True
                    break
            if not mine:
                pending_path_review_ids.append(int(pid))

    return {
        "courses": courses,
        "tracking_by_course_id": tracking_by_course_id,
        "tracked_courses": tracked_courses,
        "selected_paths": selected_paths,
        "path_details_by_id": path_details_by_id,
        "paths": paths,
        "shared_courses": shared_courses,
        "shared_paths": shared_paths,
        "articles": articles,
        "shared_articles": shared_articles,
        "course_review_summary_by_id": course_review_summary_by_id,
        "path_review_summary_by_id": path_review_summary_by_id,
        "pending_course_review_ids": pending_course_review_ids,
        "pending_path_review_ids": pending_path_review_ids,
    }
