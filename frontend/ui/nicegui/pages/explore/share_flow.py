"""Explore share dialog wiring extracted from page composition."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.pages.articles.dialogs import build_share_article_dialog
from frontend.ui.nicegui.pages.courses.dialogs import build_share_course_dialog
from frontend.ui.nicegui.pages.courses.ui_glue import parse_duration_hours
from frontend.ui.nicegui.pages.explore.controller import ExplorePageController
from frontend.ui.nicegui.pages.explore.share_models import ExploreSharePayload, ExploreUrlValue
from frontend.ui.nicegui.pages.explore.state import ExplorePageState
from frontend.ui.nicegui.pages.paths.dialogs import build_share_path_dialog


@dataclass(frozen=True, slots=True)
class ExploreShareBindings:
    """Share callbacks wired for Explore share menu targets."""

    open_share_target: Callable[[str], None]


def create_explore_share_bindings(
    *,
    controller: ExplorePageController,
    state: ExplorePageState,
    username: str,
    reload_data: Callable[[], Awaitable[None]],
    refresh_ui: Callable[..., Any],
    on_unknown_target: Callable[[str], None],
) -> ExploreShareBindings:
    """Create share callbacks and dialog openers used by Explore page."""

    async def _submit_course_share(payload: dict[str, Any]) -> dict[str, Any]:
        return await controller.create_course_share(
            state=state,
            payload=ExploreSharePayload(payload=dict(payload or {})),
            reload_data=reload_data,
            refresh_ui=refresh_ui,
        )

    open_course_share_dialog = build_share_course_dialog(
        username=username,
        parse_duration_hours=parse_duration_hours,
        on_submit=_submit_course_share,
        on_suggest_from_url=lambda url: controller.suggest_course_from_url(url_value=ExploreUrlValue(url=str(url or ""))),
        is_duplicate_url=lambda url: controller.is_duplicate_course_url(
            state=state,
            url_value=ExploreUrlValue(url=str(url or "")),
        ),
    )

    async def _submit_path_share(payload: dict[str, Any]) -> None:
        await controller.create_path_share(
            state=state,
            payload=ExploreSharePayload(payload=dict(payload or {})),
            reload_data=reload_data,
            refresh_ui=refresh_ui,
        )

    path_share_dialog, path_share_course_ids, open_path_share_dialog_raw = build_share_path_dialog(
        username=username,
        on_submit=_submit_path_share,
    )
    _ = path_share_dialog

    def _open_path_share_dialog() -> None:
        path_share_course_ids.options = controller.build_path_share_course_options(state=state)
        path_share_course_ids.update()
        open_path_share_dialog_raw()

    async def _submit_article_share(payload: dict[str, Any]) -> dict[str, Any]:
        return await controller.create_article_share(
            state=state,
            payload=ExploreSharePayload(payload=dict(payload or {})),
            reload_data=reload_data,
            refresh_ui=refresh_ui,
        )

    open_article_share_dialog = build_share_article_dialog(
        username=username,
        on_submit=_submit_article_share,
        on_suggest_from_url=lambda url: controller.suggest_article_from_url(
            url_value=ExploreUrlValue(url=str(url or ""))
        ),
        is_duplicate_url=lambda url: controller.is_duplicate_article_url(
            state=state,
            url_value=ExploreUrlValue(url=str(url or "")),
        ),
    )

    def _open_share_target(target: str) -> None:
        tab = str(target or "").strip().lower()
        if tab == "course":
            open_course_share_dialog()
            return
        if tab == "path":
            _open_path_share_dialog()
            return
        if tab == "article":
            open_article_share_dialog()
            return
        on_unknown_target(tab)

    return ExploreShareBindings(open_share_target=_open_share_target)
