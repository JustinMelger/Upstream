"""UI sections for the Explore page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.pages.explore.ui_glue import SORT_OPTIONS, TAB_OPTIONS


@dataclass
class ExploreTopbarControls:
    """Topbar controls rendered for Explore page."""

    search_input: Any
    tab_filter: Any
    sort_filter: Any
    share_btn: Any
    filters_btn: Any
    meta: Any


@dataclass
class ExploreFilterControls:
    """Drawer filter controls rendered for Explore page."""

    dialog: Any
    provider_filter: Any
    category_filter: Any
    tag_filter: Any
    author_filter: Any


def render_explore_topbar(*, initial_tab: str, on_open_filters: Any, on_open_share: Any) -> ExploreTopbarControls:
    """Render Explore topbar and return control handles."""
    with ui.column().classes("lp-topbar lp-sticky-controls lp-courses-toolbar w-full gap-2"):
        with ui.row().classes("w-full items-center gap-2"):
            search_input = (
                ui.input("Search courses, paths, and articles")
                .props("clearable debounce=300 dense")
                .classes("lp-topbar-search lp-courses-search")
                .style("flex: 1")
            )
            meta = ui.label("").classes("lp-topbar-meta lp-topbar-count lp-topbar-meta--quiet")
        with ui.row().classes("w-full items-center justify-between gap-2 flex-wrap"):
            with ui.row().classes("items-center gap-2 lp-topbar-group lp-topbar-group--secondary lp-courses-toolbar-controls"):
                ui.label("View").classes("lp-topbar-group-label")
                tab_filter = (
                    ui.radio(TAB_OPTIONS, value=initial_tab)
                    .props("inline dense")
                    .classes("text-sm lp-topbar-secondary-control")
                )
            with ui.row().classes("items-center gap-2 lp-topbar-group lp-topbar-group--secondary lp-courses-toolbar-controls"):
                ui.label("Sort").classes("lp-topbar-group-label")
                sort_filter = (
                    ui.select(SORT_OPTIONS, value="", label=None)
                    .props("dense")
                    .style("min-width: 180px")
                    .classes("lp-topbar-secondary-control")
                )
                share_btn = ui.button("Share", on_click=on_open_share).props("dense")
                filters_btn = ui.button("Filters", on_click=on_open_filters).props("dense outline").classes("lp-topbar-share")

    return ExploreTopbarControls(
        search_input=search_input,
        tab_filter=tab_filter,
        sort_filter=sort_filter,
        share_btn=share_btn,
        filters_btn=filters_btn,
        meta=meta,
    )


def render_explore_filters_dialog(*, on_reset: Any) -> ExploreFilterControls:
    """Render Explore filters drawer and return controls."""
    with ui.dialog().props("position=right") as filters_dialog:
        with ui.card().classes("lp-dialog lp-courses-filter-drawer"):
            with ui.row().classes("items-center justify-between w-full"):
                ui.label("Explore filters").classes("text-lg font-semibold")
                ui.button(icon="close", on_click=filters_dialog.close).props("flat dense")
            provider_filter = ui.select({"": "Any provider"}, label="Course provider", value="").props("dense")
            category_filter = ui.select({"": "Any category"}, label="Course category", value="").props("dense")
            tag_filter = ui.select({"": "Any tag"}, label="Article tag", value="").props("dense")
            author_filter = ui.select({"": "Anyone"}, label="Article author", value="").props("dense")
            with ui.row().classes("items-center gap-2 w-full"):
                ui.button("Reset", on_click=on_reset).props("outline dense")
                ui.button("Apply", on_click=filters_dialog.close).props("dense")

    return ExploreFilterControls(
        dialog=filters_dialog,
        provider_filter=provider_filter,
        category_filter=category_filter,
        tag_filter=tag_filter,
        author_filter=author_filter,
    )


def bind_rail_arrow_visibility(*, rail_id: str, left_btn_id: str, right_btn_id: str) -> None:
    """Bind arrow visibility and edge behavior for one horizontal rail."""
    ui.run_javascript(
        (
            "(() => {"
            f"const rail = document.getElementById('{rail_id}');"
            f"const left = document.getElementById('{left_btn_id}');"
            f"const right = document.getElementById('{right_btn_id}');"
            "if (!rail || !left || !right) return;"
            "const update = () => {"
            "  const maxScroll = Math.max(0, rail.scrollWidth - rail.clientWidth);"
            "  const x = Math.max(0, rail.scrollLeft);"
            "  if (maxScroll <= 2) { left.style.display = 'none'; right.style.display = 'none'; return; }"
            "  left.style.display = x <= 2 ? 'none' : '';"
            "  right.style.display = x >= (maxScroll - 2) ? 'none' : '';"
            "};"
            "if (!rail.dataset.lpBound) {"
            "  rail.addEventListener('scroll', update, { passive: true });"
            "  window.addEventListener('resize', update);"
            "  rail.dataset.lpBound = '1';"
            "}"
            "setTimeout(update, 0);"
            "})();"
        )
    )


def render_explore_article_rails(
    *,
    shown_articles: list[dict[str, Any]],
    render_article_item: Any,
) -> None:
    """Render grouped article rails for Explore."""
    with ui.column().classes("w-full gap-3 lp-courses-section"):
        ui.label("Articles").classes("lp-courses-section-title")
        grouped_articles: dict[str, list[dict[str, Any]]] = {}
        for row in list(shown_articles or []):
            group_name = str(row.get("_explore_group") or "General")
            grouped_articles.setdefault(group_name, []).append(row)

        for row_idx, (group_name, rows) in enumerate(grouped_articles.items()):
            rail_id = f"lp-explore-articles-rail-{row_idx}"
            left_btn_id = f"{rail_id}-left"
            right_btn_id = f"{rail_id}-right"
            with ui.column().classes("w-full gap-2"):
                with ui.row().classes("items-center justify-between w-full lp-courses-row-head"):
                    ui.label(group_name).classes("lp-courses-row-title")
                    with ui.row().classes("items-center gap-2 lp-courses-rail-controls"):
                        ui.button(
                            icon="chevron_left",
                            on_click=lambda _rid=rail_id: ui.run_javascript(
                                (
                                    "(() => {"
                                    f"const el = document.getElementById('{_rid}');"
                                    "if (el) { el.scrollBy({ left: -460, behavior: 'smooth' }); }"
                                    "})();"
                                )
                            ),
                        ).props(f'dense flat round id="{left_btn_id}"').classes("lp-rail-nav-btn")
                        ui.button(
                            icon="chevron_right",
                            on_click=lambda _rid=rail_id: ui.run_javascript(
                                (
                                    "(() => {"
                                    f"const el = document.getElementById('{_rid}');"
                                    "if (el) { el.scrollBy({ left: 460, behavior: 'smooth' }); }"
                                    "})();"
                                )
                            ),
                        ).props(f'dense flat round id="{right_btn_id}"').classes("lp-rail-nav-btn")
                with ui.element("div").classes("lp-courses-rail").props(f'id="{rail_id}"'):
                    for article in rows:
                        with ui.element("div").classes("lp-courses-rail-item"):
                            render_article_item(article)
            bind_rail_arrow_visibility(rail_id=rail_id, left_btn_id=left_btn_id, right_btn_id=right_btn_id)
