"""Form builders for learning-item share routes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import AnyHttpUrl, TypeAdapter, ValidationError

from frontend.ui.nicegui.core.learning_items import learning_item_type_label
from frontend.ui.nicegui.pages.share.helpers import (
    normalize_requested_share_type,
    share_route_for_type,
    share_title_input_label,
)


_HTTP_URL_ADAPTER: TypeAdapter[AnyHttpUrl] = TypeAdapter(AnyHttpUrl)


def normalize_http_url(raw: str) -> str:
    """Normalize and validate an HTTP(S) URL for share forms."""
    value = str(raw or "").strip()
    if not value:
        return ""
    try:
        return str(_HTTP_URL_ADAPTER.validate_python(value))
    except ValidationError:
        return ""


@dataclass(slots=True)
class CourseShareControls:
    """UI handles for course/video share routes."""

    url_input: Any
    url_hint: Any
    type_hint: Any
    import_btn: Any
    title_input: Any
    title_suggestion: Any
    apply_title_btn: Any
    description_input: Any
    provider_input: Any
    category_input: Any
    save_btn: Any
    publish_btn: Any
    preview: Any


@dataclass(slots=True)
class ArticleShareControls:
    """UI handles for article share routes."""

    url_input: Any
    url_hint: Any
    type_hint: Any
    import_btn: Any
    title_input: Any
    tags_input: Any
    suggestion_hint: Any
    save_btn: Any
    publish_btn: Any
    preview: Any


def render_share_scaffold(*, ui_module: Any, title: str, subtitle: str) -> None:
    """Render the common share-page title/subtitle block."""
    with ui_module.column().classes("w-full gap-1 lp-share-header"):
        with ui_module.row().classes("w-full items-center justify-between gap-2 flex-wrap"):
            ui_module.label("Share").classes("text-xs font-medium uppercase tracking-[0.18em]").style(
                "color: var(--lp-muted)"
            )
            ui_module.button("Back to Explore", on_click=lambda: ui_module.navigate.to("/explore")).props("flat dense")
        ui_module.label(title).classes("lp-home-title")
        ui_module.label(subtitle).classes("text-sm max-w-3xl").style("color: var(--lp-muted)")


def render_share_type_picker(*, ui_module: Any, current_type: str) -> None:
    """Render the learning-item subtype picker."""
    with ui_module.row().classes("w-full items-center gap-2 flex-wrap"):
        ui_module.label("Type").classes("text-xs").style("color: var(--lp-muted)")
        for item_type in ("video", "course", "article"):
            is_current = normalize_requested_share_type(current_type) == item_type
            btn = ui_module.button(
                learning_item_type_label(item_type),
                on_click=lambda _item_type=item_type: ui_module.navigate.to(share_route_for_type(_item_type)),
            ).props("dense" if is_current else "outline dense")
            if is_current:
                btn.classes("lp-explore-category-btn--active")


def build_course_controls(*, ui_module: Any, item_type: str) -> CourseShareControls:
    """Build controls for course/video share routes."""
    with ui_module.card().classes("lp-card w-full lp-share-surface"):
        with ui_module.row().classes("w-full items-stretch gap-4 lp-share-columns"):
            with ui_module.column().classes("grow basis-0 min-w-[320px] gap-3 lp-share-form"):
                ui_module.label("Import learning item").classes("lp-home-section-title")
                url_input = ui_module.input("https://...").props("clearable dense").classes("w-full lp-share-input")
                url_hint = ui_module.label("").classes("text-xs").style("color: var(--lp-muted)")
                type_hint = ui_module.label("").classes("text-xs").style("color: var(--lp-muted)")
                import_btn = ui_module.button("Import metadata").props("unelevated no-caps").classes("lp-share-import-btn")
                ui_module.separator()
                ui_module.label("Learning item details").classes("lp-home-section-title")
                title_input = (
                    ui_module.input(share_title_input_label(item_type))
                    .props("clearable dense")
                    .classes("w-full lp-share-input")
                )
                with ui_module.row().classes("w-full items-center justify-between lp-share-suggestion-row"):
                    title_suggestion = ui_module.label("").classes("text-xs").style("color: var(--lp-muted)")
                    apply_title_btn = ui_module.button("Apply suggestion").props("dense outline no-caps")
                description_input = (
                    ui_module.textarea("Description").props("autogrow dense maxlength=300").classes("w-full lp-share-input")
                )
                with ui_module.row().classes("w-full gap-2 lp-share-grid-two"):
                    provider_input = ui_module.input("Provider").props("clearable dense").classes("w-full lp-share-input")
                    category_input = ui_module.input("Category").props("clearable dense").classes("w-full lp-share-input")

            with ui_module.column().classes("grow basis-0 min-w-[320px] gap-3 lp-share-preview-col"):
                ui_module.label("Learning item preview").classes("lp-home-section-title")

                @ui_module.refreshable
                def preview() -> None:
                    with ui_module.card().classes("lp-card w-full lp-share-preview-card"):
                        ui_module.label(str(title_input.value or share_title_input_label(item_type))).classes(
                            "text-md font-semibold"
                        )
                        provider = str(provider_input.value or "").strip() or "Provider"
                        category = str(category_input.value or "").strip() or "Category"
                        ui_module.label(f"{provider} · {category}").classes("text-xs").style("color: var(--lp-muted)")
                        ui_module.separator()
                        ui_module.label(str(description_input.value or "Description preview")).classes("text-sm").style(
                            "color: var(--lp-muted)"
                        )
                        source_url = normalize_http_url(str(url_input.value or ""))
                        if source_url:
                            ui_module.button(
                                "Open learning item",
                                on_click=lambda u=source_url: ui_module.navigate.to(u, new_tab=True),
                            ).props("dense outline no-caps")

                preview()

        with ui_module.row().classes("w-full justify-end gap-2 mt-2 lp-share-actions"):
            save_btn = ui_module.button("Save Draft").props("dense outline no-caps").classes("lp-share-save-btn")
            publish_btn = ui_module.button("Publish Learning Item").props("unelevated no-caps").classes("lp-share-publish-btn")

    return CourseShareControls(
        url_input=url_input,
        url_hint=url_hint,
        type_hint=type_hint,
        import_btn=import_btn,
        title_input=title_input,
        title_suggestion=title_suggestion,
        apply_title_btn=apply_title_btn,
        description_input=description_input,
        provider_input=provider_input,
        category_input=category_input,
        save_btn=save_btn,
        publish_btn=publish_btn,
        preview=preview,
    )


def build_article_controls(*, ui_module: Any) -> ArticleShareControls:
    """Build controls for article share routes."""
    with ui_module.card().classes("lp-card w-full lp-share-surface"):
        with ui_module.row().classes("w-full items-stretch gap-4 lp-share-columns"):
            with ui_module.column().classes("grow basis-0 min-w-[320px] gap-3 lp-share-form"):
                ui_module.label("Import learning item").classes("lp-home-section-title")
                url_input = ui_module.input("https://...").props("clearable dense").classes("w-full lp-share-input")
                url_hint = ui_module.label("").classes("text-xs").style("color: var(--lp-muted)")
                type_hint = ui_module.label("").classes("text-xs").style("color: var(--lp-muted)")
                import_btn = ui_module.button("Import metadata").props("unelevated no-caps").classes("lp-share-import-btn")
                ui_module.separator()
                ui_module.label("Learning item details").classes("lp-home-section-title")
                title_input = (
                    ui_module.input(share_title_input_label("article"))
                    .props("clearable dense")
                    .classes("w-full lp-share-input")
                )
                tags_input = ui_module.input("Tags (comma-separated)").props("clearable dense").classes("w-full lp-share-input")
                suggestion_hint = ui_module.label("").classes("text-xs").style("color: var(--lp-muted)")

            with ui_module.column().classes("grow basis-0 min-w-[320px] gap-3 lp-share-preview-col"):
                ui_module.label("Learning item preview").classes("lp-home-section-title")

                @ui_module.refreshable
                def preview() -> None:
                    with ui_module.card().classes("lp-card w-full lp-share-preview-card"):
                        ui_module.label(str(title_input.value or "Article title")).classes("text-md font-semibold")
                        ui_module.label(str(tags_input.value or "No tags")).classes("text-xs").style("color: var(--lp-muted)")
                        source_url = normalize_http_url(str(url_input.value or ""))
                        if source_url:
                            ui_module.button(
                                "Open learning item",
                                on_click=lambda u=source_url: ui_module.navigate.to(u, new_tab=True),
                            ).props("dense outline no-caps")

                preview()

        with ui_module.row().classes("w-full justify-end gap-2 mt-2 lp-share-actions"):
            save_btn = ui_module.button("Save Draft").props("dense outline no-caps").classes("lp-share-save-btn")
            publish_btn = ui_module.button("Publish Learning Item").props("unelevated no-caps").classes("lp-share-publish-btn")

    return ArticleShareControls(
        url_input=url_input,
        url_hint=url_hint,
        type_hint=type_hint,
        import_btn=import_btn,
        title_input=title_input,
        tags_input=tags_input,
        suggestion_hint=suggestion_hint,
        save_btn=save_btn,
        publish_btn=publish_btn,
        preview=preview,
    )
