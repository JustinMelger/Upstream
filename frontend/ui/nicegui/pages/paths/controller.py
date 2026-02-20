"""Controller/state layer for the Paths NiceGUI page."""

from __future__ import annotations

import asyncio
from typing import Any

from frontend.ui.nicegui.core.api_client import ApiClient
from frontend.ui.nicegui.pages.paths.state import PathDetailBundle, PathsPageState
from frontend.ui.nicegui.services.courses_service import index_tracking_by_course_id
from frontend.ui.nicegui.services.paths_service import (
    index_courses_by_int_id,
    index_rows_by_int_id,
    load_path_recommendation_summaries,
    load_paths_page_data,
    select_path_and_seed_tracking,
    unselect_path,
)


class PathsPageController:
    """Imperative orchestration for Paths page API workflows."""

    def __init__(self, *, api: ApiClient):
        self._api = api

    async def reload_selected(self, *, state: PathsPageState) -> None:
        selected_result = await self._api.get("/paths/selected/list")
        state.selected_by_id = index_rows_by_int_id(list(selected_result or []))

    async def reload_tracking(self, *, state: PathsPageState) -> None:
        tracking_result = await self._api.get("/tracking")
        state.tracking_by_course_id = index_tracking_by_course_id(list(tracking_result or []))

    async def reload_selected_details(self, *, state: PathsPageState) -> None:
        path_ids = sorted(int(pid) for pid in state.selected_by_id.keys())
        state.selected_detail_by_path_id = {}
        if not path_ids:
            return
        results = await asyncio.gather(*(self._api.get(f"/paths/{pid}") for pid in path_ids), return_exceptions=True)
        for pid, payload in zip(path_ids, results, strict=False):
            if isinstance(payload, Exception):
                continue
            if isinstance(payload, dict):
                state.selected_detail_by_path_id[int(pid)] = payload

    async def ensure_selected_detail(self, *, path_id: int, state: PathsPageState) -> None:
        if int(path_id) in state.selected_detail_by_path_id:
            return
        detail = await self._api.get(f"/paths/{int(path_id)}")
        if isinstance(detail, dict):
            state.selected_detail_by_path_id[int(path_id)] = detail

    async def get_path_detail(self, *, path_id: int) -> dict[str, Any]:
        """Load a single path detail payload."""
        payload = await self._api.get(f"/paths/{int(path_id)}")
        return dict(payload or {}) if isinstance(payload, dict) else {}

    async def create_path(self, *, payload: dict[str, Any]) -> dict[str, Any]:
        """Create a path."""
        created = await self._api.post("/paths", dict(payload or {}))
        return dict(created or {}) if isinstance(created, dict) else {}

    async def update_path(self, *, path_id: int, payload: dict[str, Any]) -> dict[str, Any]:
        """Update a path."""
        updated = await self._api.put(f"/paths/{int(path_id)}", dict(payload or {}))
        return dict(updated or {}) if isinstance(updated, dict) else {}

    async def delete_path(self, *, path_id: int) -> bool:
        """Delete a path."""
        await self._api.delete(f"/paths/{int(path_id)}")
        return True

    async def get_path_recommendations(self, *, path_id: int) -> list[dict[str, Any]]:
        """Load recommendations rows for a path."""
        rows = await self._api.get(f"/paths/{int(path_id)}/recommendations")
        return [r for r in list(rows or []) if isinstance(r, dict)]

    async def get_user_recommendation_note(self, *, path_id: int, username: str) -> str:
        """Return current user's recommendation note for a path, if present."""
        rows = await self.get_path_recommendations(path_id=path_id)
        for row in rows:
            if str(row.get("created_by") or "") == str(username):
                return str(row.get("note") or "")
        return ""

    async def save_recommendation(self, *, path_id: int, note: str) -> dict[str, Any]:
        """Create or update current user's recommendation for a path."""
        payload = await self._api.post(f"/paths/{int(path_id)}/recommendations", {"note": str(note or "").strip()})
        return dict(payload or {}) if isinstance(payload, dict) else {}

    async def load_recommendation_summary_for_path(self, *, path_id: int) -> dict[str, Any] | None:
        """Load recommendation summary row for a single path id."""
        rows = await load_path_recommendation_summaries(api=self._api, path_ids=[int(path_id)])
        row = rows.get(int(path_id))
        return dict(row) if isinstance(row, dict) else None

    async def save_path_review(self, *, path_id: int, rating: int, text: str) -> dict[str, Any]:
        """Create or update current user's review for a path."""
        payload = await self._api.post(
            f"/paths/{int(path_id)}/reviews",
            {
                "rating": int(rating),
                "text": str(text or ""),
            },
        )
        return dict(payload or {}) if isinstance(payload, dict) else {}

    async def delete_path_review(self, *, path_id: int, review_id: int) -> bool:
        """Delete a path review by id."""
        await self._api.delete(f"/paths/{int(path_id)}/reviews/{int(review_id)}")
        return True

    async def _load_course_review_summary(self, *, course_ids: list[int]) -> dict[int, dict[str, Any]]:
        if not course_ids:
            return {}
        rows = await self._api.get("/courses/reviews/summary", params={"course_ids": [int(cid) for cid in course_ids]})
        out: dict[int, dict[str, Any]] = {}
        for row in list(rows or []):
            if not isinstance(row, dict):
                continue
            try:
                cid = int(row.get("course_id") or 0)
            except (TypeError, ValueError):
                continue
            if cid > 0:
                out[cid] = row
        return out

    async def load_path_detail_bundle(self, *, path_id: int) -> PathDetailBundle:
        """Load path detail dialog data (best-effort for social side payloads)."""
        detail = await self.get_path_detail(path_id=path_id)

        path_reviews: list[dict[str, Any]] = []
        path_recommendations: list[dict[str, Any]] = []
        try:
            reviews_result, recommendations_result = await asyncio.gather(
                self._api.get(f"/paths/{int(path_id)}/reviews"),
                self._api.get(f"/paths/{int(path_id)}/recommendations"),
            )
            path_reviews = [r for r in list(reviews_result or []) if isinstance(r, dict)]
            path_recommendations = [r for r in list(recommendations_result or []) if isinstance(r, dict)]
        except Exception:
            path_reviews = []
            path_recommendations = []

        course_ids_in_path: list[int] = []
        for c in list(detail.get("courses") or []):
            if not isinstance(c, dict):
                continue
            try:
                cid = int(c.get("id") or 0)
            except (TypeError, ValueError):
                continue
            if cid > 0:
                course_ids_in_path.append(cid)

        course_review_summary_by_course_id: dict[int, dict[str, Any]] = {}
        try:
            course_review_summary_by_course_id = await self._load_course_review_summary(course_ids=course_ids_in_path)
        except Exception:
            course_review_summary_by_course_id = {}

        return PathDetailBundle(
            detail=detail,
            path_reviews=path_reviews,
            path_recommendations=path_recommendations,
            course_review_summary_by_course_id=course_review_summary_by_course_id,
        )

    async def select_path(self, *, path_id: int, state: PathsPageState) -> tuple[int, dict[str, Any] | None]:
        cached_detail = state.selected_detail_by_path_id.get(int(path_id))
        return await select_path_and_seed_tracking(
            api=self._api,
            path_id=int(path_id),
            tracking_by_course_id=state.tracking_by_course_id,
            cached_detail=cached_detail if isinstance(cached_detail, dict) else None,
        )

    async def unselect_path(self, *, path_id: int) -> bool:
        return await unselect_path(api=self._api, path_id=int(path_id))

    async def load_all(self, *, state: PathsPageState) -> None:
        paths, selected_by_id, courses, course_by_id = await load_paths_page_data(api=self._api)
        state.paths = paths
        state.selected_by_id = selected_by_id
        state.courses = courses
        state.course_by_id = course_by_id

        await asyncio.gather(
            self.reload_tracking(state=state),
            self.reload_selected_details(state=state),
        )

        path_ids: list[int] = []
        for p in state.paths:
            if not isinstance(p, dict):
                continue
            try:
                pid = int(p.get("id") or 0)
            except (TypeError, ValueError):
                continue
            if pid > 0:
                path_ids.append(pid)

        state.path_review_summary_by_id = {}
        state.path_recommendation_summary_by_id = {}
        if not path_ids:
            return

        summaries = await self._api.get("/paths/reviews/summary", params={"path_ids": path_ids})
        state.path_recommendation_summary_by_id = await load_path_recommendation_summaries(api=self._api, path_ids=path_ids)
        for row in list(summaries or []):
            if not isinstance(row, dict):
                continue
            try:
                pid = int(row.get("path_id") or 0)
            except (TypeError, ValueError):
                continue
            if pid > 0:
                state.path_review_summary_by_id[pid] = row
