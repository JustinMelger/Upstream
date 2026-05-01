"""UI sections for the Teams page."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.feedback import render_empty_block
from frontend.ui.nicegui.pages.shared_activity.sections import render_activity_feed


def render_teams_list(
    *,
    teams: list[dict[str, Any]],
    selected_team_id: int | None,
    on_open: Callable[[int], Any],
    on_create_team: Callable[[], Any] | None = None,
) -> None:
    """Render the list of teams the user belongs to."""
    if not teams:
        render_empty_block(
            title="No teams yet.",
            description="Create your first team to start following shared learning together.",
            primary_label="Create team",
            on_primary=on_create_team,
            compact=True,
        )
        return

    with ui.column().classes("w-full gap-0 lp-teams-list"):
        for row in teams:
            team_id = int(row.get("id") or 0)
            name = str(row.get("name") or "Untitled team")
            member_count = int(row.get("member_count") or 0)
            my_role = str(row.get("my_role") or "")
            classes = "w-full lp-teams-list-row"
            if selected_team_id is not None and int(selected_team_id) == team_id:
                classes += " lp-teams-list-row--active"
            with ui.element("div").classes(classes):
                with ui.row().classes("items-start justify-between w-full gap-2"):
                    with ui.row().classes("items-start gap-2"):
                        ui.icon("groups").classes("text-[14px] mt-[2px]").style("color: var(--lp-muted)")
                        with ui.column().classes("gap-0"):
                            ui.label(name).classes("text-sm font-semibold lp-teams-list-row-title")
                            ui.label(f"{member_count} members · {my_role or 'member'}").classes(
                                "text-xs lp-teams-list-row-meta"
                            ).style("color: var(--lp-muted)")
                            ui.label("Recent updates in this team").classes("text-xs lp-teams-list-row-preview").style(
                                "color: var(--lp-muted)"
                            )
                    ui.button("Open", on_click=lambda tid=team_id: on_open(tid)).props("dense flat").classes(
                        "lp-teams-open-link"
                    )


def render_team_members(
    *,
    team: dict[str, Any],
    can_manage: bool,
    current_user: str,
    on_remove: Callable[[str], Any],
) -> None:
    """Render team members list with optional remove actions."""
    members = [row for row in list(team.get("members") or []) if isinstance(row, dict)]
    if not members:
        render_empty_block(
            title="No members yet.",
            description="Invite teammates to start collaboration in this workspace.",
            compact=True,
        )
        return

    with ui.column().classes("w-full gap-0"):
        for row in members:
            user_id = str(row.get("user_id") or "")
            role = str(row.get("role") or "member")
            with ui.row().classes("w-full items-center justify-between lp-teams-member-row"):
                with ui.row().classes("items-center gap-2"):
                    ui.icon("person", size="16px")
                    ui.label(user_id).classes("text-sm")
                    ui.badge(role).props("outline")
                if can_manage and user_id and user_id.lower() != str(current_user).lower() and role != "owner":
                    ui.button("Remove", on_click=lambda uid=user_id: on_remove(uid)).props("dense outline")
