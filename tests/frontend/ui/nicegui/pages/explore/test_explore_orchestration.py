from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.domains.paths.state import PathsPageState
from frontend.ui.nicegui.pages.explore.orchestration import (
    clear_explore_tracking_status,
    load_explore_articles_background,
    load_explore_courses,
    load_explore_paths_background,
    load_explore_videos_background,
    set_explore_tracking_status,
)
from frontend.ui.nicegui.pages.explore.state import ExplorePageState


@dataclass(slots=True)
class _CoursesBundle:
    courses: list[dict[str, Any]]
    tracking_by_course_id: dict[int, dict[str, Any]]
    review_summary_by_course_id: dict[int, dict[str, Any]]


class _CoursesController:
    def __init__(self, *, fail_load: bool = False) -> None:
        self.fail_load = bool(fail_load)
        self.calls: list[tuple[str, int, str]] = []

    async def load_list_bundle(self, *, params: Any | None) -> _CoursesBundle:
        if self.fail_load:
            raise ApiError(status_code=503, message="courses_unavailable")
        assert params is None
        return _CoursesBundle(
            courses=[{"id": 7, "title": "Async Python"}],
            tracking_by_course_id={7: {"course_id": 7, "status": "interested"}},
            review_summary_by_course_id={7: {"course_id": 7, "review_count": 3}},
        )

    async def set_tracking_status(self, *, course_id: int, status: str) -> None:
        self.calls.append(("set", int(course_id), str(status)))

    async def clear_tracking_status(self, *, course_id: int) -> None:
        self.calls.append(("clear", int(course_id), ""))


class _PathsController:
    def __init__(self, *, fail_load: bool = False, seed_tracking: bool = True) -> None:
        self.fail_load = bool(fail_load)
        self.seed_tracking = bool(seed_tracking)

    async def load_all(self, *, state: PathsPageState) -> None:
        if self.fail_load:
            raise ApiError(status_code=502, message="paths_unavailable")
        state.paths = [{"id": 11, "name": "Backend track"}]
        state.selected_by_id = {11: {"id": 11, "status": "interested"}}
        state.selected_detail_by_path_id = {11: {"id": 11, "courses": [{"id": 7}]}}
        state.path_review_summary_by_id = {11: {"path_id": 11, "review_count": 4}}
        if self.seed_tracking:
            state.tracking_by_course_id = {7: {"course_id": 7, "status": "in_progress"}}


@dataclass(slots=True)
class _ArticlesBundle:
    articles: list[dict[str, Any]]
    review_summary_by_article_id: dict[int, dict[str, Any]]


class _ArticlesController:
    def __init__(self, *, fail_load: bool = False) -> None:
        self.fail_load = bool(fail_load)

    async def load_list_bundle(self) -> _ArticlesBundle:
        if self.fail_load:
            raise ApiError(status_code=504, message="articles_timeout")
        return _ArticlesBundle(
            articles=[{"id": 21, "title": "API design"}],
            review_summary_by_article_id={21: {"article_id": 21, "review_count": 1}},
        )


@dataclass(slots=True)
class _VideosBundle:
    videos: list[dict[str, Any]]
    review_summary_by_video_id: dict[int, dict[str, Any]]


class _VideosController:
    def __init__(self, *, fail_load: bool = False) -> None:
        self.fail_load = bool(fail_load)

    async def load_list_bundle(self, *, params: Any | None) -> _VideosBundle:
        if self.fail_load:
            raise ApiError(status_code=503, message="videos_unavailable")
        assert params is None
        return _VideosBundle(
            videos=[{"id": 31, "title": "Architecture walkthrough"}],
            review_summary_by_video_id={31: {"video_id": 31, "review_count": 2}},
        )


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_explore_courses_updates_state_and_spawns_background_loads() -> None:
    state = ExplorePageState()
    controller = _CoursesController()
    events: list[str] = []

    await load_explore_courses(
        state=state,
        courses_controller=controller,
        refresh_ui=lambda: events.append("refresh"),
        refresh_filter_options=lambda: events.append("filters"),
        spawn_background_loads=lambda: events.append("spawn"),
    )

    assert state.loaded_once is True
    assert state.loading is False
    assert state.courses == [{"id": 7, "title": "Async Python"}]
    assert state.tracking_by_course_id[7]["status"] == "interested"
    assert state.course_review_summary_by_course_id[7]["review_count"] == 3
    assert events == ["refresh", "filters", "refresh", "spawn", "refresh"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_explore_paths_background_copies_payloads_and_tracking() -> None:
    state = ExplorePageState(tracking_by_course_id={99: {"course_id": 99, "status": "completed"}})
    controller = _PathsController(seed_tracking=True)
    events: list[str] = []
    warnings: list[str] = []

    await load_explore_paths_background(
        state=state,
        paths_controller=controller,
        refresh_ui=lambda: events.append("refresh"),
        notify_warning=lambda message: warnings.append(message),
    )

    assert state.paths_loading is False
    assert state.paths == [{"id": 11, "name": "Backend track"}]
    assert state.selected_by_path_id[11]["status"] == "interested"
    assert state.selected_detail_by_path_id[11]["id"] == 11
    assert state.path_review_summary_by_id[11]["review_count"] == 4
    assert state.tracking_by_course_id[7]["status"] == "in_progress"
    assert warnings == []
    assert events == ["refresh", "refresh"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_explore_paths_background_handles_errors_without_crashing() -> None:
    state = ExplorePageState(
        paths=[{"id": 1}],
        selected_by_path_id={1: {"id": 1}},
        selected_detail_by_path_id={1: {"id": 1}},
        path_review_summary_by_id={1: {"path_id": 1, "review_count": 1}},
    )
    controller = _PathsController(fail_load=True)
    warnings: list[str] = []
    events: list[str] = []

    await load_explore_paths_background(
        state=state,
        paths_controller=controller,
        refresh_ui=lambda: events.append("refresh"),
        notify_warning=lambda message: warnings.append(message),
    )

    assert state.paths == []
    assert state.selected_by_path_id == {}
    assert state.selected_detail_by_path_id == {}
    assert state.path_review_summary_by_id == {}
    assert warnings == ["502: paths_unavailable"]
    assert state.paths_loading is False
    assert events == ["refresh", "refresh"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_explore_articles_background_short_circuits_when_feature_disabled() -> None:
    state = ExplorePageState(
        articles=[{"id": 1}],
        article_review_summary_by_article_id={1: {"article_id": 1}},
    )
    controller = _ArticlesController()
    events: list[str] = []
    warnings: list[str] = []

    await load_explore_articles_background(
        state=state,
        feature_articles_enabled=False,
        articles_controller=controller,
        refresh_ui=lambda: events.append("refresh"),
        refresh_filter_options=lambda: events.append("filters"),
        notify_warning=lambda message: warnings.append(message),
    )

    assert state.articles == []
    assert state.article_review_summary_by_article_id == {}
    assert events == []
    assert warnings == []


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_explore_articles_background_handles_error_and_refreshes_filters() -> None:
    state = ExplorePageState()
    controller = _ArticlesController(fail_load=True)
    events: list[str] = []
    warnings: list[str] = []

    await load_explore_articles_background(
        state=state,
        feature_articles_enabled=True,
        articles_controller=controller,
        refresh_ui=lambda: events.append("refresh"),
        refresh_filter_options=lambda: events.append("filters"),
        notify_warning=lambda message: warnings.append(message),
    )

    assert state.articles_loading is False
    assert state.articles == []
    assert state.article_review_summary_by_article_id == {}
    assert warnings == ["504: articles_timeout"]
    assert events == ["refresh", "filters", "refresh"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_explore_videos_background_copies_payloads_and_review_summaries() -> None:
    state = ExplorePageState()
    controller = _VideosController()
    events: list[str] = []
    warnings: list[str] = []

    await load_explore_videos_background(
        state=state,
        videos_controller=controller,
        refresh_ui=lambda: events.append("refresh"),
        notify_warning=lambda message: warnings.append(message),
    )

    assert state.videos_loading is False
    assert state.videos == [{"id": 31, "title": "Architecture walkthrough"}]
    assert int(state.video_review_summary_by_video_id[31]["review_count"]) == 2
    assert warnings == []
    assert events == ["refresh", "refresh"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_load_explore_videos_background_handles_errors_without_crashing() -> None:
    state = ExplorePageState(
        videos=[{"id": 1}],
        video_review_summary_by_video_id={1: {"video_id": 1, "review_count": 1}},
    )
    controller = _VideosController(fail_load=True)
    warnings: list[str] = []
    events: list[str] = []

    await load_explore_videos_background(
        state=state,
        videos_controller=controller,
        refresh_ui=lambda: events.append("refresh"),
        notify_warning=lambda message: warnings.append(message),
    )

    assert state.videos == [{"id": 1}]
    assert state.video_review_summary_by_video_id == {1: {"video_id": 1, "review_count": 1}}
    assert warnings == ["503: videos_unavailable"]
    assert state.videos_loading is False
    assert events == ["refresh", "refresh"]


@pytest.mark.unit
@pytest.mark.anyio
async def test_set_and_clear_explore_tracking_status_mutate_state() -> None:
    state = ExplorePageState()
    controller = _CoursesController()
    events: list[str] = []

    await set_explore_tracking_status(
        state=state,
        courses_controller=controller,
        course_id=7,
        status="in_progress",
        refresh_ui=lambda: events.append("refresh"),
    )
    await clear_explore_tracking_status(
        state=state,
        courses_controller=controller,
        course_id=7,
        refresh_ui=lambda: events.append("refresh"),
    )

    assert controller.calls == [("set", 7, "in_progress"), ("clear", 7, "")]
    assert state.tracking_by_course_id == {}
    assert events == ["refresh", "refresh"]
