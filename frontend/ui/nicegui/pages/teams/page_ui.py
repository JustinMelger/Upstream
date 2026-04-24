"""UI orchestration helpers for the Teams page."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nicegui import ui

from frontend.ui.nicegui.components.feedback import render_empty_block, render_error_block
from frontend.ui.nicegui.core.api_client import ApiError
from frontend.ui.nicegui.core.errors import FrontendError, guard_ui_action, safe_notify
from frontend.ui.nicegui.core.navigation import build_activity_tab_link
from frontend.ui.nicegui.pages.shared_activity.view_model import build_activity_event_views
from frontend.ui.nicegui.pages.teams.controller import TeamsPageController
from frontend.ui.nicegui.pages.teams.sections import (
    render_inbox_activity,
    render_team_activity,
    render_team_members,
    render_teams_list,
)
from frontend.ui.nicegui.pages.teams.state import TeamsPageState


@dataclass(slots=True)
class _TeamsPageView:
    """View orchestrator for the `/teams` page."""

    controller: TeamsPageController
    state: TeamsPageState
    username: str
    role: str
    initial_tab: str

    view_tabs: Any = None
    create_team_btn: Any = None
    refresh_btn: Any = None
    create_team_dialog: Any = None
    team_name_input: Any = None
    team_description_input: Any = None
    teams_list_view: Any = None
    team_detail_view: Any = None

    def build(self) -> None:
        """Build static page shell and bind event hooks."""
        self._render_topbar()
        self._render_create_dialog()
        self._register_refreshables()
        self._render_layout()
        self._bind_actions()

    def _render_topbar(self) -> None:
        with ui.card().classes("lp-card w-full lp-teams-shell lp-teams-overview-strip"):
            with ui.row().classes("items-center justify-end gap-2 w-full lp-teams-overview-actions"):
                self.create_team_btn = ui.button("Create team").props("dense")
                self.refresh_btn = ui.button("Refresh").props("dense outline").classes("lp-teams-refresh")

    def _render_create_dialog(self) -> None:
        with ui.dialog() as create_team_dialog:
            with ui.card().classes("lp-card lp-dialog w-[min(560px,95vw)]"):
                ui.label("Create team").classes("text-lg font-semibold")
                self.team_name_input = ui.input("Team name").props("clearable")
                self.team_description_input = ui.input("Description (optional)").props("clearable")
                with ui.row().classes("w-full justify-end gap-2"):
                    ui.button("Cancel", on_click=create_team_dialog.close).props("flat")
                    ui.button("Create", on_click=self._submit_create_team).props("dense")
        self.create_team_dialog = create_team_dialog

    def _register_refreshables(self) -> None:
        self.teams_list_view = ui.refreshable(self._render_teams_list_view)
        self.team_detail_view = ui.refreshable(self._render_team_detail_view)

    def _render_layout(self) -> None:
        if not self.state.teams:
            with ui.element("div").classes("lp-teams-empty-workspace"):
                with ui.column().classes("w-full gap-2 lp-teams-empty-main"):
                    ui.label("Start one team workspace").classes("lp-teams-empty-title")
                    ui.label("Create a team first. Once members join, Inbox and Team activity become your team follow-up space.").classes(
                        "text-sm lp-teams-empty-copy"
                    ).style("color: var(--lp-muted)")
                    with ui.row().classes("items-center gap-2 flex-wrap"):
                        ui.button("Create team", on_click=self.create_team_dialog.open).props("dense")
                        ui.button("Refresh", on_click=self.refresh_all).props("dense outline").classes("lp-teams-refresh")
                with ui.element("div").classes("lp-teams-empty-hints"):
                    with ui.element("div").classes("lp-teams-empty-hint"):
                        ui.label("1").classes("lp-chip lp-chip--sky")
                        with ui.column().classes("gap-0"):
                            ui.label("Create a team").classes("text-sm font-semibold")
                            ui.label("Set up one workspace for shared learning.").classes("text-xs").style(
                                "color: var(--lp-muted)"
                            )
                    with ui.element("div").classes("lp-teams-empty-hint"):
                        ui.label("2").classes("lp-chip lp-chip--sky")
                        with ui.column().classes("gap-0"):
                            ui.label("Invite teammates").classes("text-sm font-semibold")
                            ui.label("Add members so reviews and updates have people to follow them.").classes("text-xs").style(
                                "color: var(--lp-muted)"
                            )
                    with ui.element("div").classes("lp-teams-empty-hint"):
                        ui.label("3").classes("lp-chip lp-chip--sky")
                        with ui.column().classes("gap-0"):
                            ui.label("Use inbox and activity").classes("text-sm font-semibold")
                            ui.label("Follow review requests and shared updates from one place.").classes("text-xs").style(
                                "color: var(--lp-muted)"
                            )
            with ui.column().classes("w-full gap-2 lp-teams-empty-inbox"):
                ui.label("Inbox").classes("text-sm font-semibold")
                render_inbox_activity(
                    inbox_rows=build_activity_event_views(events=self.state.inbox_rows),
                    on_open_target=self.open_activity_target,
                )
            return

        with ui.element("div").classes("lp-teams-workspace-grid"):
            with ui.column().classes("w-full gap-2 lp-teams-sidebar"):
                ui.label("Workspace").classes("text-xs lp-teams-sidebar-title")
                self.view_tabs = (
                    ui.radio(
                        {"inbox": "Inbox", "my_teams": "My teams", "team": "Team activity"},
                        value=self.initial_tab,
                    )
                    .props("dense")
                    .classes("text-sm lp-teams-tabs lp-teams-side-nav")
                )
            with ui.column().classes("w-full gap-3"):
                self.teams_list_view()
            with ui.column().classes("w-full gap-3"):
                self.team_detail_view()

    def _bind_actions(self) -> None:
        self.create_team_btn.on_click(self.create_team_dialog.open)
        self.refresh_btn.on_click(self.refresh_all)
        if self.view_tabs is not None:
            self.view_tabs.on("update:model-value", self.on_tab_change)

    def _render_teams_list_view(self) -> None:
        with ui.card().classes("lp-card w-full lp-teams-shell lp-teams-list-shell"):
            with ui.row().classes("items-center justify-between w-full"):
                ui.label("My teams").classes("text-lg font-semibold lp-teams-list-title")
                if self.state.teams:
                    ui.label(f"{len(self.state.teams)} total").classes("text-xs lp-teams-list-count").style(
                        "color: var(--lp-muted)"
                    )
            ui.separator()
            if self.state.error_message and not self.state.teams:
                render_error_block(
                    title="Could not load teams.",
                    message=self.state.error_message,
                    retry_label="Retry",
                    on_retry=self.refresh_all,
                )
                return
            render_teams_list(
                teams=self.state.teams,
                selected_team_id=self.state.selected_team_id,
                on_open=self.open_team,
                on_create_team=self.create_team_dialog.open,
            )

    def _render_team_detail_view(self) -> None:
        with ui.column().classes("w-full gap-3"):
            current_tab = self._current_tab()
            if current_tab == "inbox":
                if self.state.error_message and not self.state.inbox_rows:
                    render_error_block(
                        title="Could not load inbox.",
                        message=self.state.error_message,
                        retry_label="Retry",
                        on_retry=self.refresh_all,
                    )
                    return
                ui.label("Inbox").classes("text-sm font-semibold")
                render_inbox_activity(
                    inbox_rows=build_activity_event_views(events=self.state.inbox_rows),
                    on_open_target=self.open_activity_target,
                )
                return

            if self.state.error_message and not self.state.selected_team:
                render_error_block(
                    title="Could not load team.",
                    message=self.state.error_message,
                    retry_label="Retry",
                    on_retry=self.refresh_all,
                )
                return
            if not self.state.selected_team:
                render_empty_block(
                    title="Select a team",
                    description="Choose a team on the left to view members and activity.",
                )
                return
            self._render_selected_team_panel(dict(self.state.selected_team))

    def _render_selected_team_panel(self, team: dict[str, Any]) -> None:
        my_role = str(team.get("my_role") or "")
        can_manage = my_role in {"owner", "admin"} or self.role == "admin"
        members = [row for row in list(team.get("members") or []) if isinstance(row, dict)]
        members_count = len(members)

        with ui.card().classes("lp-card w-full lp-teams-shell lp-teams-workspace-shell"):
            with ui.row().classes("items-start justify-between w-full"):
                with ui.column().classes("gap-1"):
                    ui.label(str(team.get("name") or "Untitled team")).classes("text-lg font-semibold lp-teams-workspace-title")
                    description = str(team.get("description") or "").strip()
                    if description:
                        ui.label(description).classes("text-sm").style("color: var(--lp-muted)")
                    ui.label(f"Owner: {str(team.get('owner_user_id') or '')}").classes("text-xs").style(
                        "color: var(--lp-muted)"
                    )
                    with ui.row().classes("items-center gap-3 flex-wrap lp-teams-workspace-meta"):
                        ui.label(f"Members: {members_count}").classes("text-xs").style("color: var(--lp-muted)")
                        ui.label(f"Role: {my_role or 'member'}").classes("text-xs").style("color: var(--lp-muted)")
                with ui.row().classes("items-center gap-2"):
                    if can_manage:
                        ui.button(
                            "Invite members",
                            on_click=lambda: ui.navigate.to(build_activity_tab_link(tab="my_teams")),
                        ).props("dense outline")
            ui.separator()

            current_tab = self._current_tab()
            if current_tab == "team":
                ui.label("Team activity").classes("text-sm font-semibold")
                render_team_activity(
                    activity_rows=build_activity_event_views(events=self.state.activity_rows),
                    on_open_target=self.open_activity_target,
                )
                return

            ui.label("Members").classes("text-sm font-semibold")
            render_team_members(
                team=team,
                can_manage=can_manage,
                current_user=self.username,
                on_remove=self.remove_member,
            )
            if can_manage:
                ui.separator()
                ui.label("Add member").classes("text-sm font-semibold")
                self._render_add_member_form(team_id=int(team.get("id") or 0))

    def _render_add_member_form(self, *, team_id: int) -> None:
        with ui.row().classes("w-full items-end gap-2 flex-wrap"):
            member_input = ui.input("Username").props("clearable")
            member_role = ui.select(
                {"member": "Member", "admin": "Admin"},
                value="member",
                label="Role",
            ).props("dense")

            @guard_ui_action(title="Add member failed")
            async def _on_add_member() -> None:
                value = str(member_input.value or "").strip()
                role_value = str(member_role.value or "member").strip().lower()
                if not value:
                    safe_notify("Username is required.", type="negative")
                    return
                try:
                    await self.controller.add_member(team_id=team_id, user_id=value, role=role_value)
                except ApiError as exc:
                    if exc.status_code == 404:
                        safe_notify("User not found.", type="negative")
                        return
                    raise
                member_input.value = ""
                member_role.value = "member"
                safe_notify("Member updated.", type="positive")
                await self.refresh_all()

            ui.button("Add member", on_click=_on_add_member).props("dense outline")

    @guard_ui_action(title="Create team failed")
    async def _submit_create_team(self) -> None:
        name = str(self.team_name_input.value or "").strip()
        description = str(self.team_description_input.value or "").strip()
        if not name:
            safe_notify("Team name is required.", type="negative")
            return
        team = await self.controller.create_team(name=name, description=description or None)
        self.create_team_dialog.close()
        self.team_name_input.value = ""
        self.team_description_input.value = ""
        safe_notify("Team created.", type="positive")
        try:
            self.state.selected_team_id = int(team.get("id") or 0)
        except (TypeError, ValueError):
            self.state.selected_team_id = None
        ui.navigate.to(build_activity_tab_link(tab="my_teams"))

    @guard_ui_action(title="Load teams failed")
    async def refresh_all(self) -> None:
        if self.state.loading:
            return
        self.state.loading = True
        try:
            self.state.teams = await self.controller.list_my_teams()
            if self.view_tabs is None and self.state.teams:
                ui.navigate.to(build_activity_tab_link(tab="my_teams"))
                return
            self._sync_selected_team_id()
            await self.refresh_selected_team()
            self.state.error_message = None
        except (ApiError, RuntimeError) as exc:
            self.state.error_message = str(exc)
            self.state.selected_team = None
            self.state.inbox_rows = []
            self.state.activity_rows = []
            if not self.state.teams:
                raise FrontendError(status_code=500, message=str(exc)) from exc
        finally:
            self.state.loading = False
            self.teams_list_view.refresh()
            self.team_detail_view.refresh()

    def _sync_selected_team_id(self) -> None:
        if self.state.selected_team_id is None:
            self.state.selected_team_id = int(self.state.teams[0].get("id") or 0) if self.state.teams else None
            return
        team_ids = {int(row.get("id") or 0) for row in self.state.teams}
        if int(self.state.selected_team_id) not in team_ids:
            self.state.selected_team_id = int(self.state.teams[0].get("id") or 0) if self.state.teams else None

    @guard_ui_action(title="Load team failed")
    async def refresh_selected_team(self) -> None:
        self.state.selected_team = None
        self.state.activity_rows = []
        current_tab = self._current_tab()
        if current_tab == "inbox":
            self.state.inbox_rows = await self.controller.list_inbox(limit=40)
        if self.state.selected_team_id is None:
            self.teams_list_view.refresh()
            self.team_detail_view.refresh()
            return

        self.state.selected_team = await self.controller.get_team_detail(team_id=int(self.state.selected_team_id))
        if current_tab == "team":
            self.state.activity_rows = await self.controller.list_activity(team_id=int(self.state.selected_team_id), limit=40)
        self.teams_list_view.refresh()
        self.team_detail_view.refresh()

    @guard_ui_action(title="Open team failed")
    async def open_team(self, team_id: int) -> None:
        self.state.selected_team_id = int(team_id)
        if self._current_tab() == "inbox":
            self.view_tabs.value = "my_teams"
        await self.refresh_all()

    @guard_ui_action(title="Remove member failed")
    async def remove_member(self, user_id: str) -> None:
        if self.state.selected_team_id is None:
            return
        removed = await self.controller.remove_member(team_id=int(self.state.selected_team_id), user_id=str(user_id))
        if removed > 0:
            safe_notify("Member removed.", type="positive")
        await self.refresh_all()

    def open_activity_target(self, target: Any) -> None:
        ui.navigate.to(str(target.open_url))

    @guard_ui_action(title="Switch tab failed")
    async def on_tab_change(self, *_args: Any) -> None:
        current = self._current_tab()
        ui.navigate.to(build_activity_tab_link(tab=current))
        if current == "inbox":
            self.state.inbox_rows = await self.controller.list_inbox(limit=40)
        if current == "team" and self.state.selected_team_id is not None:
            self.state.activity_rows = await self.controller.list_activity(team_id=int(self.state.selected_team_id), limit=40)
        self.team_detail_view.refresh()

    def _current_tab(self) -> str:
        return str(getattr(self.view_tabs, "value", "inbox") or "inbox")
