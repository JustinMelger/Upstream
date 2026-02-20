from __future__ import annotations

import pytest

from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.pages.courses.orchestration import (
    open_delete_course_confirmation,
    perform_clear_tracking,
    perform_create_course,
    perform_delete_course,
    perform_delete_course_from_dialog,
    perform_set_tracking,
    perform_update_course,
    refresh_course_recommendation_summary,
    reload_tracking_only,
)
from frontend.ui.nicegui.pages.courses.state import CoursesPageState


class _Controller:
    def __init__(self) -> None:
        self.calls: list[tuple[str, int, str]] = []
        self.fail_reload = False
        self.summary_row: dict | None = {"course_id": 7, "recommendation_count": 4}
        self.cache_cleared: list[tuple[int, str]] = []

    async def reload_tracking(self) -> dict[int, dict]:
        if self.fail_reload:
            raise ApiError(status_code=503, message="tracking_unavailable")
        return {7: {"course_id": 7, "status": "interested"}}

    async def set_tracking_status(self, *, course_id: int, status: str) -> None:
        self.calls.append(("set", int(course_id), str(status)))

    async def clear_tracking_status(self, *, course_id: int) -> None:
        self.calls.append(("clear", int(course_id), ""))

    async def load_recommendation_summary_for_course(self, *, course_id: int) -> dict | None:
        return self.summary_row

    def clear_course_detail_cache(self, *, course_id: int, cache_scope: str) -> None:
        self.cache_cleared.append((int(course_id), str(cache_scope)))

    async def create_course(self, *, payload: dict) -> dict:
        self.calls.append(("create", int(payload.get("id") or 0), str(payload.get("title") or "")))
        return payload

    async def update_course(self, *, course_id: int, payload: dict) -> dict:
        self.calls.append(("update", int(course_id), str(payload.get("title") or "")))
        return payload

    async def delete_course(self, *, course_id: int) -> bool:
        self.calls.append(("delete", int(course_id), ""))
        return True


@pytest.mark.unit
@pytest.mark.anyio
async def test_reload_tracking_only_handles_api_error() -> None:
    controller = _Controller()
    controller.fail_reload = True
    state = CoursesPageState(tracking_by_course_id={1: {"course_id": 1, "status": "completed"}})
    events: list[str] = []
    errors: list[str] = []

    ok = await reload_tracking_only(
        page_state=state,
        controller=controller,
        recompute_facet_options=lambda: events.append("recompute"),
        refresh_courses_list_ui=lambda: events.append("refresh"),
        notify_error=lambda message: errors.append(message),
    )

    assert ok is False
    assert state.tracking_by_course_id == {}
    assert errors == ["503: tracking_unavailable"]
    assert events == ["refresh"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_perform_set_tracking_calls_controller_and_reload() -> None:
    controller = _Controller()
    state = CoursesPageState()
    events: list[str] = []

    ok = await perform_set_tracking(
        course_id=7,
        status="in_progress",
        controller=controller,
        page_state=state,
        recompute_facet_options=lambda: events.append("recompute"),
        refresh_courses_list_ui=lambda: events.append("refresh"),
        notify_error=lambda _message: events.append("error"),
    )

    assert ok is True
    assert ("set", 7, "in_progress") in controller.calls
    assert state.tracking_by_course_id[7]["status"] == "interested"
    assert events == ["recompute", "refresh"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_perform_clear_tracking_calls_controller_and_reload() -> None:
    controller = _Controller()
    state = CoursesPageState()
    events: list[str] = []

    ok = await perform_clear_tracking(
        course_id=7,
        controller=controller,
        page_state=state,
        recompute_facet_options=lambda: events.append("recompute"),
        refresh_courses_list_ui=lambda: events.append("refresh"),
        notify_error=lambda _message: events.append("error"),
    )

    assert ok is True
    assert ("clear", 7, "") in controller.calls
    assert events == ["recompute", "refresh"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_refresh_course_recommendation_summary_updates_state_and_cache() -> None:
    controller = _Controller()
    state = CoursesPageState()
    refreshed: list[str] = []

    await refresh_course_recommendation_summary(
        course_id=7,
        username="alice",
        controller=controller,
        page_state=state,
        refresh_courses_list_ui=lambda: refreshed.append("refresh"),
    )

    assert state.recommendation_summary_by_course_id[7]["recommendation_count"] == 4
    assert controller.cache_cleared == [(7, "alice")]
    assert refreshed == ["refresh"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_perform_create_course_calls_controller_then_reload() -> None:
    controller = _Controller()
    events: list[str] = []

    async def _reload() -> None:
        events.append("reload")

    await perform_create_course(
        payload={"id": 7, "title": "FastAPI"},
        controller=controller,
        reload_page=_reload,
    )

    assert ("create", 7, "FastAPI") in controller.calls
    assert events == ["reload"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_perform_update_course_calls_controller_then_reload() -> None:
    controller = _Controller()
    events: list[str] = []

    async def _reload() -> None:
        events.append("reload")

    await perform_update_course(
        course_id=9,
        payload={"title": "Updated"},
        controller=controller,
        reload_page=_reload,
    )

    assert ("update", 9, "Updated") in controller.calls
    assert events == ["reload"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_perform_delete_course_calls_controller_then_reload() -> None:
    controller = _Controller()
    events: list[str] = []

    async def _reload() -> None:
        events.append("reload")

    await perform_delete_course(
        course_id=11,
        controller=controller,
        reload_page=_reload,
    )

    assert ("delete", 11, "") in controller.calls
    assert events == ["reload"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_perform_delete_course_from_dialog_accepts_positional_id() -> None:
    controller = _Controller()
    events: list[str] = []

    async def _reload() -> None:
        events.append("reload")

    await perform_delete_course_from_dialog(
        13,
        controller=controller,
        reload_page=_reload,
    )

    assert ("delete", 13, "") in controller.calls
    assert events == ["reload"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_open_delete_course_confirmation_calls_dialog_with_callback() -> None:
    called: list[tuple[int, bool]] = []

    async def _on_delete(course_id: int) -> None:
        called.append((int(course_id), True))

    async def _open_delete_dialog(*, course_id: int, on_delete):  # noqa: ANN001
        await on_delete(int(course_id))

    await open_delete_course_confirmation(
        17,
        open_delete_dialog=_open_delete_dialog,
        on_delete_course=_on_delete,
    )

    assert called == [(17, True)]
