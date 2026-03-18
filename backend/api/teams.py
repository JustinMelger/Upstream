from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query

from backend.api.deps import get_teams_service, require_session
from backend.api.schemas import (
    TeamActivityItem,
    TeamCreateRequest,
    TeamDetailPayload,
    TeamMemberAddRequest,
    TeamMemberDeleteResponse,
    TeamMemberPayload,
    TeamPayload,
)
from backend.services.teams_service import TeamsService


router = APIRouter(prefix="/teams", tags=["teams"])


@router.post("", response_model=TeamDetailPayload)
async def create_team(
    payload: TeamCreateRequest,
    current_user: str = Depends(require_session),
    teams: TeamsService = Depends(get_teams_service),
) -> dict[str, Any]:
    """Create a team owned by the current user."""
    return await teams.create_team(current_user=current_user, payload=payload.model_dump())


@router.get("/mine", response_model=list[TeamPayload])
async def list_my_teams(
    current_user: str = Depends(require_session),
    teams: TeamsService = Depends(get_teams_service),
) -> list[dict[str, Any]]:
    """List teams the current user belongs to."""
    return await teams.list_my_teams(current_user=current_user)


@router.get("/{team_id}", response_model=TeamDetailPayload)
async def get_team(
    team_id: int,
    current_user: str = Depends(require_session),
    teams: TeamsService = Depends(get_teams_service),
) -> dict[str, Any]:
    """Get team detail for a team the user belongs to."""
    return await teams.get_team(team_id=int(team_id), current_user=current_user)


@router.post("/{team_id}/members", response_model=TeamMemberPayload)
async def add_team_member(
    team_id: int,
    payload: TeamMemberAddRequest,
    current_user: str = Depends(require_session),
    teams: TeamsService = Depends(get_teams_service),
) -> dict[str, Any]:
    """Add or update a member in a team (owner/admin only)."""
    return await teams.add_member(team_id=int(team_id), payload=payload.model_dump(), current_user=current_user)


@router.delete("/{team_id}/members/{user_id}", response_model=TeamMemberDeleteResponse)
async def remove_team_member(
    team_id: int,
    user_id: str,
    current_user: str = Depends(require_session),
    teams: TeamsService = Depends(get_teams_service),
) -> dict[str, int]:
    """Remove a member from a team (owner/admin only)."""
    removed = await teams.remove_member(team_id=int(team_id), user_id=user_id, current_user=current_user)
    return {"removed": int(removed)}


@router.get("/{team_id}/activity", response_model=list[TeamActivityItem])
async def get_team_activity(
    team_id: int,
    limit: int = Query(default=30, ge=1, le=100),
    current_user: str = Depends(require_session),
    teams: TeamsService = Depends(get_teams_service),
) -> list[dict[str, Any]]:
    """Return team-scoped activity feed events."""
    return await teams.list_activity(team_id=int(team_id), current_user=current_user, limit=int(limit))
