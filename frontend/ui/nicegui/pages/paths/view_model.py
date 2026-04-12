"""Presentation helpers (ViewModel) for the Paths page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from frontend.ui.nicegui.core.datetime_utils import is_recent, parse_iso_datetime
from frontend.ui.nicegui.core.learning_items import normalize_learning_item_type
from frontend.ui.nicegui.core.summary_formatters import format_review_summary as _format_review


@dataclass(slots=True)
class PathCardView:
    """Display fields for a single path card."""

    is_new: bool
    is_updated: bool
    rating_badge: str
    shared_by: str
    tracking_label_text: str
    tracking_chip_cls: str
    completed: int
    total_courses: int
    progress: float
    milestone: str
    milestone_class: str
    impact: str
    next_title: str
    card_class_suffix: str


def format_review_summary(row: dict[str, Any] | None) -> str:
    """Format a path review summary row into a compact label."""
    return _format_review(row, style="fraction")


def format_rating_badge(row: dict[str, Any] | None) -> str:
    """Format a compact rating badge for path cards (e.g., '4.2/5 (12)')."""
    return format_review_summary(row)


def path_tracking_label(is_tracked: bool) -> str:
    """Return path tracking label for cards/details."""
    return "Tracked" if is_tracked else "Not tracked"


def path_tracking_chip_class(is_tracked: bool) -> str:
    """Return chip class for path tracking state."""
    return "lp-chip lp-chip--sky" if is_tracked else "lp-chip lp-chip--muted"


def compute_outcomes(
    *,
    detail: dict[str, Any],
    tracking_by_course_id: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    """Compute path milestone + next-step metadata for UX rendering."""
    completed, total, ratio = _compute_path_progress(detail=detail, tracking_by_course_id=tracking_by_course_id)
    courses = _path_course_rows(detail=detail)
    has_learning_items = _has_learning_items(detail=detail)
    next_course: dict[str, Any] | None = None
    in_progress = 0
    for c in courses:
        try:
            cid = int(c.get("id") or 0)
        except (TypeError, ValueError):
            continue
        status = str((tracking_by_course_id.get(cid) or {}).get("status") or "").strip()
        if status == "in_progress":
            in_progress += 1
        if next_course is None and status != "completed":
            next_course = c

    remaining = max(0, int(total) - int(completed))
    if total <= 0:
        milestone = "Reference path" if has_learning_items else "No learning items"
        milestone_class = "lp-chip lp-chip--muted"
        impact = (
            "Add a course to enable progress tracking." if has_learning_items else "Add learning items to define this path."
        )
    elif remaining == 0:
        milestone = "Completed"
        milestone_class = "lp-chip lp-chip--lime"
        impact = "All courses completed."
    elif completed <= 0:
        milestone = "Not started"
        milestone_class = "lp-chip lp-chip--muted"
        impact = f"{remaining} course(s) left to complete this path."
    elif ratio >= 0.5:
        milestone = "Halfway"
        milestone_class = "lp-chip lp-chip--teal"
        impact = f"{remaining} course(s) left to complete this path."
    else:
        milestone = "Started"
        milestone_class = "lp-chip lp-chip--sky"
        impact = f"{remaining} course(s) left to complete this path."

    if in_progress > 0 and remaining > 0:
        impact = f"{impact} {in_progress} in progress."

    return {
        "completed": completed,
        "total": total,
        "ratio": ratio,
        "next_course": next_course,
        "milestone": milestone,
        "milestone_class": milestone_class,
        "impact": impact,
    }


def _compute_path_progress(
    *,
    detail: dict[str, Any],
    tracking_by_course_id: dict[int, dict[str, Any]],
) -> tuple[int, int, float]:
    courses = _path_course_rows(detail=detail)
    total = len(courses)
    completed = 0
    for c in courses:
        raw = c.get("id")
        if raw is None:
            continue
        try:
            cid = int(raw)
        except (TypeError, ValueError):
            continue
        if str((tracking_by_course_id.get(cid) or {}).get("status") or "") == "completed":
            completed += 1
    ratio = (completed / total) if total else 0.0
    return completed, total, ratio


def _path_course_rows(*, detail: dict[str, Any]) -> list[dict[str, Any]]:
    """Return ordered course rows from typed items."""
    items = [row for row in list(detail.get("items") or []) if isinstance(row, dict)]
    return [row for row in items if normalize_learning_item_type(str(row.get("type") or ""), default="course") == "course"]


def _has_learning_items(*, detail: dict[str, Any]) -> bool:
    """Return whether the path contains any learning items at all."""
    items = [row for row in list(detail.get("items") or []) if isinstance(row, dict)]
    return bool(items)


def enrich_path_courses(
    *,
    courses: list[dict[str, Any]] | None,
    review_summary_by_course_id: dict[int, dict[str, Any]] | None,
    tracking_by_course_id: dict[int, dict[str, Any]] | None,
) -> list[dict[str, Any]]:
    """Attach review/tracking presentation fields used by the path detail table."""

    def _tracking_status(cid: int) -> str:
        return str((tracking_by_course_id or {}).get(int(cid), {}).get("status") or "").strip()

    out: list[dict[str, Any]] = []
    for course in list(courses or []):
        try:
            cid = int(course.get("id") or 0)
        except (TypeError, ValueError):
            cid = 0
        row = (review_summary_by_course_id or {}).get(cid)
        out.append(
            dict(
                course,
                reviews=format_review_summary(row),
                tracking_status=_tracking_status(cid),
            )
        )
    return out


def summarize_path_reviews(*, path_id: int, reviews: list[dict[str, Any]] | None) -> dict[str, Any]:
    """Compute path summary row from current reviews list."""
    ratings: list[int] = []
    for row in list(reviews or []):
        try:
            ratings.append(int(row.get("rating") or 0))
        except (TypeError, ValueError):
            continue
    if not ratings:
        return {"path_id": int(path_id), "avg_rating": 0.0, "review_count": 0}
    avg = float(sum(ratings)) / float(len(ratings))
    return {"path_id": int(path_id), "avg_rating": float(avg), "review_count": int(len(ratings))}


def map_path_card_view(
    *,
    path_row: dict[str, Any],
    is_tracked: bool,
    detail: dict[str, Any] | None,
    tracking_by_course_id: dict[int, dict[str, Any]],
    review_summary_row: dict[str, Any] | None,
) -> PathCardView:
    """Map path + state payloads to card display values."""
    outcomes: dict[str, Any] = {}
    completed = 0
    total_courses = 0
    progress = 0.0
    if is_tracked and isinstance(detail, dict):
        outcomes = compute_outcomes(detail=detail, tracking_by_course_id=tracking_by_course_id)
        completed = int(outcomes.get("completed") or 0)
        total_courses = int(outcomes.get("total") or 0)
        progress = float(outcomes.get("ratio") or 0.0)

    created_at = parse_iso_datetime(path_row.get("created_at"))
    updated_at = parse_iso_datetime(path_row.get("updated_at"))
    is_updated = is_recent(updated_at) and created_at is not None and updated_at is not None and updated_at > created_at
    is_new = (not is_updated) and is_recent(created_at)

    next_course = outcomes.get("next_course") if isinstance(outcomes, dict) else None
    next_title = str(next_course.get("title") or "").strip() if isinstance(next_course, dict) else ""

    return PathCardView(
        is_new=is_new,
        is_updated=is_updated,
        rating_badge=format_rating_badge(review_summary_row),
        shared_by=str(path_row.get("created_by") or "").strip(),
        tracking_label_text=path_tracking_label(is_tracked),
        tracking_chip_cls=path_tracking_chip_class(is_tracked),
        completed=int(completed if is_tracked else 0),
        total_courses=int(total_courses if is_tracked else 0),
        progress=float(progress if is_tracked else 0.0),
        milestone=str(outcomes.get("milestone") or "") if is_tracked else "",
        milestone_class=str(outcomes.get("milestone_class") or "") if is_tracked else "",
        impact=str(outcomes.get("impact") or "") if is_tracked else "",
        next_title=next_title,
        card_class_suffix=" lp-accent-card--interested" if is_tracked else "",
    )
