"""Backward-compatible re-export for path item helpers.

Shared path-item helpers now live in ``frontend.ui.nicegui.core.path_items`` so
service modules can depend on them without importing page-package code.
"""

from frontend.ui.nicegui.core.path_items import (
    build_path_item_payloads,
    count_course_items,
    decode_path_item_ref,
    encode_path_item_ref,
    learning_item_option_label,
    path_course_ids,
)
