"""UI sections for the Explore page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.core.a11y import apply_icon_button_a11y
from frontend.ui.nicegui.pages.explore.ui_glue import SORT_OPTIONS, TAB_OPTIONS


@dataclass
class ExploreTopbarControls:
    """Topbar controls rendered for Explore page."""

    search_input: Any
    tab_filter: Any
    sort_filter: Any
    share_btn: Any
    filters_btn: Any | None
    meta: Any


@dataclass
class ExploreFilterControls:
    """Drawer filter controls rendered for Explore page."""

    dialog: Any
    provider_filter: Any
    category_filter: Any
    tag_filter: Any
    author_filter: Any


def render_explore_share_dialog(*, on_share_learning_item: Any, on_share_path: Any) -> Any:
    """Render share dialog and return dialog handle."""

    def _close_then_share_learning_item(dialog: Any) -> None:
        dialog.close()
        on_share_learning_item()

    def _close_then_share_path(dialog: Any) -> None:
        dialog.close()
        on_share_path()

    with ui.dialog() as share_dialog:
        with ui.card().classes("lp-card lp-dialog w-[min(540px,95vw)]"):
            ui.label("Share learning").classes("text-lg font-semibold")
            ui.label("Choose what you want to share.").classes("text-sm").style("color: var(--lp-muted)")

            with ui.column().classes("w-full gap-2 mt-2"):
                ui.button(
                    "Share learning item",
                    on_click=lambda: _close_then_share_learning_item(share_dialog),
                ).props("unelevated")
                ui.button(
                    "Share path",
                    on_click=lambda: _close_then_share_path(share_dialog),
                ).props("outline")
            with ui.row().classes("justify-end w-full mt-1"):
                ui.button("Cancel", on_click=share_dialog.close).props("flat")
    return share_dialog


def render_explore_topbar(*, initial_tab: str, on_open_share: Any) -> ExploreTopbarControls:
    """Render Explore topbar and return control handles."""
    with ui.column().classes("lp-topbar lp-sticky-controls lp-courses-toolbar lp-explore-toolbar lp-explore-control-card w-full gap-3"):
        with ui.row().classes("w-full items-center gap-2 flex-wrap"):
            search_input = (
                ui.input("Search learning content")
                .props("clearable debounce=300 dense")
                .classes("lp-topbar-search lp-courses-search lp-transition-field")
                .style("flex: 1")
            )
            meta = ui.label("").classes("lp-topbar-meta lp-topbar-count lp-topbar-meta--quiet")
            share_btn = ui.button("Share", on_click=on_open_share).props("unelevated color=primary")
        with ui.row().classes("w-full items-center gap-2 flex-wrap"):
            with ui.row().classes("items-center gap-2 lp-topbar-group lp-topbar-group--secondary lp-courses-toolbar-controls"):
                ui.label("Filters").classes("lp-topbar-group-label")
                tab_filter = (
                    ui.radio(TAB_OPTIONS, value=initial_tab)
                    .props("inline dense")
                    .classes("text-sm lp-topbar-secondary-control")
                )
            ui.space()
            with ui.row().classes("items-center gap-2 lp-topbar-group lp-topbar-group--secondary lp-courses-toolbar-controls"):
                ui.label("Sort").classes("lp-topbar-group-label")
                sort_filter = (
                    ui.select(SORT_OPTIONS, value="", label=None)
                    .props("dense")
                    .style("min-width: 180px")
                    .classes("lp-topbar-secondary-control lp-transition-field")
                )

    return ExploreTopbarControls(
        search_input=search_input,
        tab_filter=tab_filter,
        sort_filter=sort_filter,
        share_btn=share_btn,
        filters_btn=None,
        meta=meta,
    )


def render_explore_filters_dialog(*, on_reset: Any) -> ExploreFilterControls:
    """Render Explore filters drawer and return controls."""
    with ui.dialog().props("position=right") as filters_dialog:
        with ui.card().classes("lp-dialog lp-courses-filter-drawer"):
            with ui.row().classes("items-center justify-between w-full"):
                ui.label("Explore filters").classes("text-lg font-semibold")
                apply_icon_button_a11y(
                    ui.button(icon="close", on_click=filters_dialog.close).props("flat dense"),
                    label="Close filters panel",
                    tooltip="Close",
                )
            provider_filter = (
                ui.select({"": "Any provider"}, label="Course provider", value="").props("dense").classes("lp-transition-field")
            )
            category_filter = (
                ui.select({"": "Any category"}, label="Course category", value="").props("dense").classes("lp-transition-field")
            )
            tag_filter = ui.select({"": "Any tag"}, label="Article tag", value="").props("dense").classes("lp-transition-field")
            author_filter = (
                ui.select({"": "Anyone"}, label="Article author", value="").props("dense").classes("lp-transition-field")
            )
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


def render_explore_spotlight_strip(
    *,
    title: str,
    description: str,
    shared_by: str,
    on_primary: Any,
) -> None:
    """Render a compact spotlight strip for Explore without hero-card height."""
    with ui.element("div").classes("lp-explore-spotlight-strip"):
        with ui.column().classes("gap-1"):
            ui.label(str(title or "Top pick")).classes("lp-explore-spotlight-title")
            if str(description or "").strip():
                ui.label(str(description)).classes("lp-explore-spotlight-body")
            if str(shared_by or "").strip():
                ui.label(f"Shared by {shared_by}").classes("lp-explore-spotlight-meta")
        ui.button("Open details", on_click=on_primary).props("dense unelevated")


def bind_rail_arrow_visibility(*, rail_id: str, left_btn_id: str, right_btn_id: str) -> None:
    """Bind arrow visibility and edge behavior for one horizontal rail."""
    ui.run_javascript(
        (
            "(() => {"
            f"const rail = document.getElementById('{rail_id}');"
            f"const left = document.getElementById('{left_btn_id}');"
            f"const right = document.getElementById('{right_btn_id}');"
            "if (!rail || !left || !right) return;"
            "rail.scrollLeft = 0;"
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
    max_groups: int | None = None,
    min_group_size: int = 1,
    overflow_group_title: str = "More for you",
    prioritize_larger_groups: bool = False,
) -> None:
    """Render grouped article rails for Explore."""
    with ui.column().classes("w-full gap-3 lp-courses-section"):
        ui.label("Articles").classes("lp-courses-section-title")
        grouped_articles: dict[str, list[dict[str, Any]]] = {}
        for row in list(shown_articles or []):
            group_name = str(row.get("_explore_group") or "General")
            grouped_articles.setdefault(group_name, []).append(row)

        if int(min_group_size) > 1:
            compacted: dict[str, list[dict[str, Any]]] = {}
            overflow_rows: list[dict[str, Any]] = []
            for group_name, rows in grouped_articles.items():
                if len(rows) < int(min_group_size):
                    overflow_rows.extend(rows)
                else:
                    compacted[group_name] = rows
            if overflow_rows:
                compacted.setdefault(str(overflow_group_title or "More for you"), []).extend(overflow_rows)
            grouped_articles = compacted

        groups: list[tuple[str, list[dict[str, Any]]]] = list(grouped_articles.items())
        if bool(prioritize_larger_groups):
            groups = sorted(groups, key=lambda item: len(item[1]), reverse=True)
        if max_groups is not None and int(max_groups) > 0 and len(groups) > int(max_groups):
            keep_count = max(1, int(max_groups) - 1)
            visible = groups[:keep_count]
            hidden = groups[keep_count:]
            hidden_rows: list[dict[str, Any]] = []
            for _, rows in hidden:
                hidden_rows.extend(rows)
            if hidden_rows:
                visible.append((str(overflow_group_title or "More for you"), hidden_rows))
            groups = visible

        for row_idx, (group_name, rows) in enumerate(groups):
            rail_id = f"lp-explore-articles-rail-{row_idx}"
            left_btn_id = f"{rail_id}-left"
            right_btn_id = f"{rail_id}-right"
            with ui.column().classes("w-full gap-2"):
                with ui.row().classes("items-center justify-between w-full lp-courses-row-head"):
                    ui.label(group_name).classes("lp-courses-row-title")
                    with ui.row().classes("items-center gap-2 lp-courses-rail-controls"):
                        left_btn = (
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
                            )
                            .props(f'dense flat round id="{left_btn_id}"')
                            .classes("lp-rail-nav-btn")
                        )
                        apply_icon_button_a11y(left_btn, label=f"Scroll {group_name} left", tooltip="Scroll left")
                        right_btn = (
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
                            )
                            .props(f'dense flat round id="{right_btn_id}"')
                            .classes("lp-rail-nav-btn")
                        )
                        apply_icon_button_a11y(right_btn, label=f"Scroll {group_name} right", tooltip="Scroll right")
                with ui.element("div").classes("lp-courses-rail").props(f'id="{rail_id}"'):
                    for article in rows:
                        render_article_item(article, item_classes="lp-courses-rail-item")
            bind_rail_arrow_visibility(rail_id=rail_id, left_btn_id=left_btn_id, right_btn_id=right_btn_id)
