from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from pydantic import StrictInt, StrictStr, ValidationError
from pydantic.dataclasses import dataclass
from sqlalchemy.exc import IntegrityError

from backend.core.errors import error_handler, F, ServiceError
from backend.database.async_repositories.teams import TeamsRepository
from backend.database.models import TeamMemberRecord, TeamRecord
from backend.database.tx import session_scope
from backend.services.auth_service import AuthService


class TeamsServiceError(ServiceError):
    """Domain error for team management failures."""


def teams_error_handler(
    message: str = "An unexpected error occurred while handling teams",
    status_code: int = 500,
) -> Callable[[F], F]:
    """Wrap uncaught team-service errors into a domain ServiceError."""
    return error_handler(
        service_error=TeamsServiceError,
        message=message,
        status_code=status_code,
        log_message="Teams service error",
    )


@dataclass
class TeamCreatePayload:
    """Typed payload for team creation."""

    name: StrictStr
    description: StrictStr | None = None


@dataclass
class TeamAddMemberPayload:
    """Typed payload for add-member mutations."""

    user_id: StrictStr
    role: StrictStr = "member"


@dataclass
class TeamActivityQueryPayload:
    """Typed payload for team activity queries."""

    limit: StrictInt = 30


class TeamsService:
    """Service for creating and managing teams and memberships."""

    def __init__(self, repo: TeamsRepository, auth: AuthService):
        """Initialize service with persistence and auth dependencies."""
        self._repo = repo
        self._auth = auth

    @staticmethod
    def _parse_create_team_payload(payload: dict) -> TeamCreatePayload:
        """Parse and validate create-team payload."""
        try:
            return TeamCreatePayload(**dict(payload or {}))
        except ValidationError as exc:
            raise TeamsServiceError(detail="invalid_payload", status_code=400) from exc

    @staticmethod
    def _parse_add_member_payload(payload: dict) -> TeamAddMemberPayload:
        """Parse and validate add-member payload."""
        try:
            return TeamAddMemberPayload(**dict(payload or {}))
        except ValidationError as exc:
            raise TeamsServiceError(detail="invalid_payload", status_code=400) from exc

    @staticmethod
    def _parse_activity_query_payload(payload: dict) -> TeamActivityQueryPayload:
        """Parse and validate team-activity query payload."""
        try:
            return TeamActivityQueryPayload(**dict(payload or {}))
        except ValidationError as exc:
            raise TeamsServiceError(detail="invalid_payload", status_code=400) from exc

    @staticmethod
    def _is_manager_role(role: str) -> bool:
        """Return whether a team role can manage members."""
        return str(role).strip().lower() in {"owner", "admin"}

    async def _load_team_or_raise(self, *, team_id: int) -> TeamRecord:
        """Fetch team or raise not_found."""
        team = await self._repo.get_team_by_id(team_id=int(team_id))
        if not team:
            raise TeamsServiceError(detail="not_found", status_code=404)
        return team

    async def _load_membership(self, *, team_id: int, user_id: str) -> TeamMemberRecord | None:
        """Fetch team membership for one user."""
        return await self._repo.get_member(team_id=int(team_id), user_id=str(user_id))

    async def _can_manage_members(self, *, team_id: int, current_user: str) -> bool:
        """Return whether the user can manage team members."""
        if await self._auth.is_admin(current_user):
            return True
        membership = await self._load_membership(team_id=int(team_id), user_id=str(current_user))
        if not membership:
            return False
        return self._is_manager_role(membership.role)

    async def _require_member_or_admin(self, *, team_id: int, current_user: str) -> TeamMemberRecord | None:
        """Require that current user is team member or site admin."""
        if await self._auth.is_admin(current_user):
            return None
        membership = await self._load_membership(team_id=int(team_id), user_id=str(current_user))
        if not membership:
            raise TeamsServiceError(detail="forbidden", status_code=403)
        return membership

    @staticmethod
    def _normalize_add_member_inputs(data: TeamAddMemberPayload) -> tuple[str, str]:
        """Normalize and validate add-member input fields."""
        user_id = str(data.user_id or "").strip()
        role = str(data.role or "member").strip().lower()
        if not user_id:
            raise TeamsServiceError(detail="missing_user_id", status_code=400)
        if role not in {"owner", "admin", "member"}:
            raise TeamsServiceError(detail="invalid_role", status_code=400)
        return user_id, role

    @staticmethod
    def _validate_owner_assignment(*, team: TeamRecord, user_id: str, role: str) -> None:
        """Ensure owner role assignments remain consistent with the team owner."""
        if role == "owner" and str(team.owner_user_id).lower() != user_id.lower():
            raise TeamsServiceError(detail="invalid_role", status_code=400)

    async def _upsert_member(self, *, team_id: int, user_id: str, role: str, now: str) -> None:
        """Create or update one team membership row."""
        existing = await self._repo.get_member(team_id=int(team_id), user_id=user_id)
        if existing:
            await self._repo.update_member_role(team_id=int(team_id), user_id=user_id, role=role, updated_at=now)
            return
        try:
            await self._repo.create_member(
                team_id=int(team_id),
                user_id=user_id,
                role=role,
                created_at=now,
                updated_at=now,
            )
        except IntegrityError as exc:
            raise TeamsServiceError(detail="membership_conflict", status_code=409) from exc

    @staticmethod
    def _serialize_membership_record(membership: TeamMemberRecord) -> dict:
        """Serialize one membership record for API responses."""
        return {
            "team_id": int(membership.team_id),
            "user_id": membership.user_id,
            "role": membership.role,
            "created_at": membership.created_at,
            "updated_at": membership.updated_at,
        }

    @teams_error_handler()
    async def create_team(self, *, current_user: str, payload: dict) -> dict:
        """Create a team for an authenticated user and add owner membership."""
        data = self._parse_create_team_payload(payload)
        name = str(data.name or "").strip()
        description = str(data.description).strip() if data.description is not None else None
        if not name:
            raise TeamsServiceError(detail="missing_name", status_code=400)
        now = datetime.now(timezone.utc).isoformat()

        async with session_scope(self._repo.session):
            team_id = await self._repo.create_team(
                name=name,
                description=description,
                owner_user_id=str(current_user),
                created_at=now,
                updated_at=now,
            )
            await self._repo.create_member(
                team_id=team_id,
                user_id=str(current_user),
                role="owner",
                created_at=now,
                updated_at=now,
            )

        return await self.get_team(team_id=int(team_id), current_user=str(current_user))

    @teams_error_handler()
    async def list_my_teams(self, *, current_user: str) -> list[dict]:
        """List teams for a user (membership based)."""
        async with session_scope(self._repo.session):
            teams = await self._repo.list_teams_for_user(user_id=str(current_user))

        out: list[dict] = []
        for team in teams:
            out.append(await self._serialize_team(team=team, current_user=current_user, include_members=False))
        return out

    @teams_error_handler()
    async def get_team(self, *, team_id: int, current_user: str) -> dict:
        """Get one team by id with members if authorized."""
        async with session_scope(self._repo.session):
            team = await self._load_team_or_raise(team_id=int(team_id))
            await self._require_member_or_admin(team_id=int(team_id), current_user=str(current_user))
        return await self._serialize_team(team=team, current_user=current_user, include_members=True)

    async def _serialize_team(self, *, team: TeamRecord, current_user: str, include_members: bool) -> dict:
        """Serialize team row and optional members for API payloads."""
        team_id = int(team.id)
        async with session_scope(self._repo.session):
            members = await self._repo.list_members(team_id=team_id)
        my_role = ""
        for member in members:
            if member.user_id.lower() == str(current_user).lower():
                my_role = member.role
                break
        if not my_role and await self._auth.is_admin(current_user):
            my_role = "admin"

        payload: dict[str, object] = {
            "id": team_id,
            "name": team.name,
            "description": team.description or "",
            "owner_user_id": team.owner_user_id,
            "created_at": team.created_at,
            "updated_at": team.updated_at,
            "member_count": len(members),
            "my_role": my_role,
        }
        if include_members:
            payload["members"] = [
                {
                    "team_id": int(member.team_id),
                    "user_id": member.user_id,
                    "role": member.role,
                    "created_at": member.created_at,
                    "updated_at": member.updated_at,
                }
                for member in members
            ]
        return payload

    @teams_error_handler()
    async def add_member(self, *, team_id: int, payload: dict, current_user: str) -> dict:
        """Add a member to a team (owner/admin only)."""
        data = self._parse_add_member_payload(payload)
        user_id, role = self._normalize_add_member_inputs(data)
        team_id_value = int(team_id)
        current_username = str(current_user)

        async with session_scope(self._repo.session):
            team = await self._load_team_or_raise(team_id=team_id_value)
            if not await self._can_manage_members(team_id=team_id_value, current_user=current_username):
                raise TeamsServiceError(detail="forbidden", status_code=403)
            self._validate_owner_assignment(team=team, user_id=user_id, role=role)
            user = await self._auth.get_user(user_id)
            if not user:
                raise TeamsServiceError(detail="user_not_found", status_code=404)
            now = datetime.now(timezone.utc).isoformat()
            await self._upsert_member(team_id=team_id_value, user_id=user_id, role=role, now=now)
            await self._repo.set_team_updated_at(team_id=team_id_value, updated_at=now)

        membership = await self._load_membership(team_id=team_id_value, user_id=user_id)
        if not membership:
            raise TeamsServiceError(detail="create_failed", status_code=500)
        return self._serialize_membership_record(membership)

    @teams_error_handler()
    async def remove_member(self, *, team_id: int, user_id: str, current_user: str) -> int:
        """Remove a team member (owner/admin only, cannot remove owner)."""
        candidate_user_id = str(user_id or "").strip()
        if not candidate_user_id:
            raise TeamsServiceError(detail="missing_user_id", status_code=400)

        async with session_scope(self._repo.session):
            team = await self._load_team_or_raise(team_id=int(team_id))
            can_manage = await self._can_manage_members(team_id=int(team_id), current_user=str(current_user))
            if not can_manage:
                raise TeamsServiceError(detail="forbidden", status_code=403)

            if str(team.owner_user_id).lower() == candidate_user_id.lower():
                raise TeamsServiceError(detail="cannot_remove_owner", status_code=400)

            existing = await self._repo.get_member(team_id=int(team_id), user_id=candidate_user_id)
            if not existing:
                raise TeamsServiceError(detail="member_not_found", status_code=404)

            removed = await self._repo.delete_member(team_id=int(team_id), user_id=candidate_user_id)
            if removed > 0:
                await self._repo.set_team_updated_at(team_id=int(team_id), updated_at=datetime.now(timezone.utc).isoformat())
            return int(removed)

    @teams_error_handler()
    async def list_activity(self, *, team_id: int, current_user: str, limit: int = 30) -> list[dict]:
        """List team-scoped activity events."""
        data = self._parse_activity_query_payload({"limit": limit})
        safe_limit = max(1, min(int(data.limit or 30), 100))

        async with session_scope(self._repo.session):
            _ = await self._load_team_or_raise(team_id=int(team_id))
            await self._require_member_or_admin(team_id=int(team_id), current_user=str(current_user))
            rows = await self._repo.list_team_activity_rows(team_id=int(team_id), limit=safe_limit)

        return [self._serialize_activity_event(row=row) for row in rows]

    @staticmethod
    def _serialize_activity_event(*, row: dict) -> dict:
        """Serialize one activity row with user-facing message."""
        event_type = str(row.get("event_type") or "")
        actor = str(row.get("actor") or "")
        target_type = str(row.get("target_type") or "")
        target_id = int(row.get("target_id") or 0)
        message = TeamsService._activity_message(event_type=event_type, actor=actor, target_type=target_type)
        return {
            "event_id": str(row.get("event_id") or ""),
            "event_type": event_type,
            "created_at": str(row.get("created_at") or ""),
            "actor": actor,
            "message": message,
            "target_type": target_type,
            "target_id": target_id,
            "target_label": f"{target_type}:{target_id}" if target_type and target_id > 0 else "",
        }

    @staticmethod
    def _activity_message(*, event_type: str, actor: str, target_type: str) -> str:
        """Build concise activity feed copy."""
        action_map = {
            "course_review": "reviewed a course",
            "path_review": "reviewed a path",
            "article_review": "reviewed an article",
        }
        action = action_map.get(str(event_type), f"updated {target_type}")
        return f"{actor} {action}".strip()
