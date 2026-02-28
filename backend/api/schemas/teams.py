from __future__ import annotations

from pydantic import StrictInt, StrictStr

from backend.api.schemas.common import APIModel


class TeamCreateRequest(APIModel):
    """Create team request payload."""

    name: StrictStr
    description: StrictStr | None = None


class TeamMemberAddRequest(APIModel):
    """Add/update team member request payload."""

    user_id: StrictStr
    role: StrictStr = "member"


class TeamMemberPayload(APIModel):
    """Team membership payload."""

    team_id: StrictInt
    user_id: StrictStr
    role: StrictStr
    created_at: StrictStr
    updated_at: StrictStr


class TeamPayload(APIModel):
    """Team payload."""

    id: StrictInt
    name: StrictStr
    description: StrictStr
    owner_user_id: StrictStr
    created_at: StrictStr
    updated_at: StrictStr
    member_count: StrictInt
    my_role: StrictStr


class TeamDetailPayload(TeamPayload):
    """Team detail payload including member list."""

    members: list[TeamMemberPayload]


class TeamMemberDeleteResponse(APIModel):
    """Delete team member response payload."""

    removed: StrictInt


class TeamActivityItem(APIModel):
    """Team-scoped activity event payload."""

    event_id: StrictStr
    event_type: StrictStr
    created_at: StrictStr
    actor: StrictStr
    message: StrictStr
    target_type: StrictStr
    target_id: StrictInt
    target_label: StrictStr
