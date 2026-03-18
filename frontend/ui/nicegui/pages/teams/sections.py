"""UI sections for the Teams page."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.feedback import render_empty_block
from frontend.ui.nicegui.core.feed_copy import team_activity_empty_description
from frontend.ui.nicegui.pages.activity.ui_glue import format_when


def render_teams_list(
    *,
    teams: list[dict[str, Any]],
    selected_team_id: int | None,
    on_open: Callable[[int], Any],
) -> None:
    """Render the list of teams the user belongs to."""
    if not teams:
        render_empty_block(
            title="No teams yet.",
            description="Create your first team to start sharing and reviewing together.",
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


def render_team_activity(
    *,
    activity_rows: list[Any],
    on_open_target: Callable[[Any], Any],
) -> None:
    """Render team activity feed for currently selected team."""
    if not activity_rows:
        render_empty_block(
            title="No team activity yet.",
            description=team_activity_empty_description(),
            compact=True,
        )
        return

    with ui.column().classes("w-full gap-0 lp-teams-activity-feed"):
        for event in activity_rows:
            actor = str(event.actor or "")
            message = str(event.message or "Activity update")
            created_at = str(event.created_at or "")
            target_meta = " · ".join(
                part
                for part in [
                    str(event.target.target_type_label or "").strip(),
                    str(event.target.interaction_label or "").strip(),
                    str(event.target.target_label or "").strip(),
                ]
                if part
            )
            with ui.element("div").classes("lp-teams-feed-row"):
                with ui.row().classes("w-full items-center justify-between gap-2"):
                    with ui.row().classes("items-start gap-2"):
                        initials = "".join(part[:1] for part in actor.split() if part)[:2].upper() or actor[:2].upper() or "TM"
                        ui.label(initials).classes("lp-home-avatar-chip")
                        with ui.column().classes("gap-1"):
                            ui.label(message).classes("text-sm lp-teams-feed-row-title")
                            ui.label(actor).classes("text-xs lp-teams-feed-row-meta").style("color: var(--lp-muted)")
                            if target_meta:
                                ui.label(target_meta).classes("text-xs lp-teams-feed-row-meta").style("color: var(--lp-muted)")
                    with ui.column().classes("items-end gap-1"):
                        ui.label(format_when(created_at)).classes("text-xs").style("color: var(--lp-muted)")
                        ui.button("Open", on_click=lambda target=event.target: on_open_target(target)).props(
                            "dense flat"
                        ).classes("lp-teams-open-link")


def render_inbox_activity(
    *,
    inbox_rows: list[Any],
    on_open_target: Callable[[Any], Any],
) -> None:
    """Render personal inbox feed rows."""
    if not inbox_rows:
        render_empty_block(
            title="No conversations pending.",
            description="Review requests and replies from teammates will appear here.",
            compact=True,
        )
        return

    with ui.column().classes("w-full gap-0 lp-teams-activity-feed"):
        for event in inbox_rows:
            actor = str(event.actor or "")
            message = str(event.message or "Activity update")
            created_at = str(event.created_at or "")
            target_meta = " · ".join(
                part
                for part in [
                    str(event.target.target_type_label or "").strip(),
                    str(event.target.interaction_label or "").strip(),
                    str(event.target.target_label or "").strip(),
                ]
                if part
            )
            with ui.element("div").classes("lp-teams-feed-row"):
                with ui.row().classes("w-full items-center justify-between gap-2"):
                    with ui.row().classes("items-start gap-2"):
                        initials = "".join(part[:1] for part in actor.split() if part)[:2].upper() or actor[:2].upper() or "TM"
                        ui.label(initials).classes("lp-home-avatar-chip")
                        with ui.column().classes("gap-1"):
                            ui.label(message).classes("text-sm lp-teams-feed-row-title")
                            ui.label(actor).classes("text-xs lp-teams-feed-row-meta").style("color: var(--lp-muted)")
                            if target_meta:
                                ui.label(target_meta).classes("text-xs lp-teams-feed-row-meta").style("color: var(--lp-muted)")
                    with ui.column().classes("items-end gap-1"):
                        ui.label(format_when(created_at)).classes("text-xs").style("color: var(--lp-muted)")
                        ui.button("Open", on_click=lambda target=event.target: on_open_target(target)).props(
                            "dense flat"
                        ).classes("lp-teams-open-link")
