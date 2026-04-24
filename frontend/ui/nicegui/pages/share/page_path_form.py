"""Form builders for path share routes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class PathShareControls:
    """UI handles for path share routes."""

    name_input: Any
    description_input: Any
    item_refs_input: Any
    save_btn: Any
    publish_btn: Any
    preview: Any


def render_share_scaffold(*, ui_module: Any, title: str, subtitle: str) -> None:
    """Render the common path share title/subtitle block."""
    with ui_module.column().classes("w-full gap-1 lp-share-header"):
        with ui_module.row().classes("w-full items-center justify-between gap-2 flex-wrap"):
            ui_module.label("Share").classes("text-xs font-medium uppercase tracking-[0.18em]").style(
                "color: var(--lp-muted)"
            )
            ui_module.button("Back to Explore", on_click=lambda: ui_module.navigate.to("/explore")).props("flat dense")
        ui_module.label(title).classes("lp-home-title")
        ui_module.label(subtitle).classes("text-sm max-w-3xl").style("color: var(--lp-muted)")


def build_path_controls(*, ui_module: Any, learning_item_options: dict[str, str]) -> PathShareControls:
    """Build controls for path share routes."""
    with ui_module.card().classes("lp-card w-full lp-share-surface"):
        with ui_module.row().classes("w-full items-stretch gap-4 lp-share-columns"):
            with ui_module.column().classes("grow basis-0 min-w-[320px] gap-3 lp-share-form"):
                ui_module.label("Path details").classes("lp-home-section-title")
                name_input = ui_module.input("Path name").props("clearable dense").classes("w-full lp-share-input")
                description_input = (
                    ui_module.textarea("Description").props("autogrow dense maxlength=400").classes("w-full lp-share-input")
                )
                item_refs_input = (
                    ui_module.select(learning_item_options, label="Learning items in order", multiple=True)
                    .props("dense")
                    .classes("w-full lp-share-input")
                )

            with ui_module.column().classes("grow basis-0 min-w-[320px] gap-3 lp-share-preview-col"):
                ui_module.label("Path preview").classes("lp-home-section-title")

                @ui_module.refreshable
                def preview() -> None:
                    with ui_module.card().classes("lp-card w-full lp-share-preview-card"):
                        ui_module.label(str(name_input.value or "Path name")).classes("text-md font-semibold")
                        selected_refs = list(item_refs_input.value or [])
                        ui_module.label(f"{len(selected_refs)} learning items selected").classes("text-xs").style(
                            "color: var(--lp-muted)"
                        )
                        ui_module.separator()
                        ui_module.label(str(description_input.value or "Path description preview")).classes("text-sm").style(
                            "color: var(--lp-muted)"
                        )

                preview()

        with ui_module.row().classes("w-full justify-end gap-2 mt-2 lp-share-actions"):
            save_btn = ui_module.button("Save Draft").props("dense outline no-caps").classes("lp-share-save-btn")
            publish_btn = ui_module.button("Publish Path").props("unelevated no-caps").classes("lp-share-publish-btn")

    return PathShareControls(
        name_input=name_input,
        description_input=description_input,
        item_refs_input=item_refs_input,
        save_btn=save_btn,
        publish_btn=publish_btn,
        preview=preview,
    )
