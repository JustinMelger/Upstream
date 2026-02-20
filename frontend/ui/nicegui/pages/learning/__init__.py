"""Learning page package exports."""

from frontend.ui.nicegui.pages.learning.page import (
    _build_course_navigation_url,
    _build_path_navigation_url,
    _next_from_tracked_courses,
    _next_uncompleted_course_from_selected_paths,
    _progress_for_path_detail,
    _recommendation_summary_label,
    _review_summary_label,
    register,
)


__all__ = [
    "register",
    "_build_course_navigation_url",
    "_build_path_navigation_url",
    "_next_from_tracked_courses",
    "_next_uncompleted_course_from_selected_paths",
    "_progress_for_path_detail",
    "_recommendation_summary_label",
    "_review_summary_label",
]
