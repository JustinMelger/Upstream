"""Reusable reviews panel for NiceGUI dialogs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable

from nicegui import ui
from pydantic import BaseModel, ConfigDict

from frontend.ui.nicegui.core.errors import guard_ui_action, safe_notify


class ReviewPanelText(BaseModel):
    """Text labels/messages for the reusable reviews panel."""

    model_config = ConfigDict(frozen=True)

    section_title: str = "Reviews"
    empty_text: str = "No reviews yet."
    save_label: str = "Save review"
    save_success_text: str = "Review saved"
    delete_success_text: str = "Review deleted"
    save_error_title: str = "Review submit failed"
    delete_error_title: str = "Delete review failed"


@dataclass(slots=True)
class ReviewPanelHooks:
    """Optional hooks for date formatting and parent-state synchronization."""

    format_date: Callable[[Any], str] | None = None
    on_changed: Callable[[list[dict[str, Any]]], None] | None = None


def _find_review_by_user(*, reviews: list[dict[str, Any]], username: str) -> dict[str, Any] | None:
    for row in reviews:
        if str(row.get("created_by") or "") == username:
            return dict(row)
    return None


def _review_input_defaults(*, my_review: dict[str, Any] | None) -> tuple[int, str]:
    rating = int((my_review or {}).get("rating") or 5)
    text = str((my_review or {}).get("text") or "")
    return rating, text


def _merge_saved_review_rows(
    *,
    reviews: list[dict[str, Any]],
    username: str,
    saved: dict[str, Any],
) -> list[dict[str, Any]]:
    """Return review rows replacing the current user's review with the saved one."""
    try:
        saved_id = int((saved or {}).get("id") or 0)
    except (TypeError, ValueError):
        saved_id = 0

    out: list[dict[str, Any]] = []
    for row in reviews:
        if str(row.get("created_by") or "") == username:
            continue
        if saved_id:
            try:
                if int(row.get("id") or 0) == saved_id:
                    continue
            except (TypeError, ValueError):
                pass
        out.append(dict(row))
    out.insert(0, dict(saved))
    return out


def render_reviews_panel(
    *,
    username: str,
    is_admin: bool,
    reviews: list[dict[str, Any]],
    on_save: Callable[[int, str], Awaitable[dict[str, Any]]],
    on_delete: Callable[[int], Awaitable[bool | None]],
    text: ReviewPanelText | None = None,
    hooks: ReviewPanelHooks | None = None,
) -> None:
    """Render a review list + editor block with in-place updates."""
    resolved_text = text if text is not None else ReviewPanelText()
    resolved_hooks = hooks if hooks is not None else ReviewPanelHooks()
    ui.label(resolved_text.section_title).classes("text-lg font-semibold")

    def _notify_changed() -> None:
        if resolved_hooks.on_changed is not None:
            resolved_hooks.on_changed(reviews)

    my_review = _find_review_by_user(reviews=reviews, username=username)

    @guard_ui_action(title=resolved_text.delete_error_title)
    async def _delete_review(review_id: int) -> None:
        nonlocal my_review
        await on_delete(int(review_id))
        reviews[:] = [r for r in reviews if int(r.get("id") or 0) != int(review_id)]
        my_review = _find_review_by_user(reviews=reviews, username=username)
        if my_review is None:
            rating_in.value = 5
            text_in.value = ""
            my_review_label.text = "Add a review"
        _notify_changed()
        reviews_list.refresh()
        safe_notify(resolved_text.delete_success_text, type="positive")

    @ui.refreshable
    def reviews_list() -> None:
        with ui.column().classes("w-full gap-2"):
            if not reviews:
                ui.label(resolved_text.empty_text).classes("text-sm").style("color: var(--lp-muted)")
                return
            for r in reviews[:20]:
                try:
                    rating = int(r.get("rating") or 0)
                except (TypeError, ValueError):
                    rating = 0
                who = str(r.get("created_by") or "").strip()
                when_raw = r.get("created_at")
                when = resolved_hooks.format_date(when_raw) if resolved_hooks.format_date else str(when_raw or "").strip()
                text = str(r.get("text") or "").strip()

                with ui.card().classes("lp-card w-full"):
                    with ui.row().classes("items-start justify-between w-full"):
                        ui.label(f"Rating: {max(1, min(5, rating))}/5 · {who}").classes("text-sm font-semibold")
                        can_delete = is_admin or (who == username)
                        if can_delete:

                            async def _do_delete(_rid: int = int(r.get("id") or 0)) -> None:
                                await _delete_review(_rid)

                            ui.button("Delete", on_click=_do_delete).props("dense color=negative outline")

                    if when:
                        ui.label(when).classes("text-xs").style("color: var(--lp-muted)")
                    if text:
                        ui.label(text).classes("text-sm text-gray-600")

    reviews_list()

    my_review_label = ui.label("Your review" if my_review else "Add a review").classes("text-md font-semibold mt-2")
    default_rating, default_text = _review_input_defaults(my_review=my_review)
    rating_in = ui.select(
        {1: "1", 2: "2", 3: "3", 4: "4", 5: "5"},
        value=default_rating,
        label="Rating",
    ).props("dense")
    text_in = ui.textarea("Comment (optional)", value=default_text).props("autogrow").classes("w-full")

    @guard_ui_action(title=resolved_text.save_error_title)
    async def _submit_review() -> None:
        saved = await on_save(int(rating_in.value or 0), str(text_in.value or ""))
        if isinstance(saved, dict):
            reviews[:] = _merge_saved_review_rows(reviews=reviews, username=username, saved=saved)
        _notify_changed()
        my_review_label.text = "Your review" if _find_review_by_user(reviews=reviews, username=username) else "Add a review"
        reviews_list.refresh()
        safe_notify(resolved_text.save_success_text, type="positive")

    with ui.row().classes("justify-end mt-2"):
        ui.button(resolved_text.save_label, on_click=_submit_review).props("outline")
