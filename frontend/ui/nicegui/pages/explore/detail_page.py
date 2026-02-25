"""Compatibility exports for Explore dedicated detail routes."""

from frontend.ui.nicegui.pages.explore.detail_article import render_explore_article_detail_page
from frontend.ui.nicegui.pages.explore.detail_course import render_explore_course_detail_page
from frontend.ui.nicegui.pages.explore.detail_path import render_explore_path_detail_page


__all__ = [
    "render_explore_article_detail_page",
    "render_explore_course_detail_page",
    "render_explore_path_detail_page",
]
