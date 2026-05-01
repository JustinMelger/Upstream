"""AI curation endpoints (draft planning only)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import require_session
from backend.api.schemas.ai import AiPlanRequest, AiPlanResponse
from backend.services.ai_curator_service import AiCuratorService


router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/plan", response_model=AiPlanResponse)
async def create_plan(
    payload: AiPlanRequest,
    _current_user: str = Depends(require_session),
) -> dict[str, Any]:
    """Return a draft learning plan for a user's goal.

    This endpoint does not write to the database.

    Args:
        payload: Plan request payload.
        _current_user: Authenticated username.

    Returns:
        Draft path and ordered draft course list.
    """
    goal = (payload.goal or "").strip()
    if not goal:
        raise HTTPException(status_code=400, detail="missing_goal")

    curator = AiCuratorService()
    draft_path, draft_courses = curator.plan(goal=goal)

    return {
        "goal": goal,
        "path": {"name": draft_path.name, "description": draft_path.description},
        "courses": [
            {
                "title": c.title,
                "description": c.description,
                "provider": c.provider,
                "category": c.category,
                "level": c.level,
                "duration_hours": c.duration_hours,
                "url": c.url,
            }
            for c in draft_courses
        ],
    }
