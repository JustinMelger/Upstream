"""Courses page package (migration in progress)."""

from frontend.ui.nicegui.pages.courses.page import _normalize_course_view_mode, _parse_duration_hours, register

__all__ = ["register", "_parse_duration_hours", "_normalize_course_view_mode"]
