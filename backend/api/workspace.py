"""React read APIs: discovery, personal progress, and shared activity."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from backend.api.deps import get_workspace_service, require_session
from backend.api.schemas.workspace import (
    ActivityEvent,
    ActivityFilters,
    CatalogFilters,
    CatalogItem,
    FacetFilters,
    LearningFilters,
    LearningItem,
    LearningSummary,
    Page,
    PathProgress,
)
from backend.services.workspace_service import WorkspaceService


router = APIRouter(tags=["workspace"])
Service = Annotated[WorkspaceService, Depends(get_workspace_service)]
User = Annotated[str, Depends(require_session)]


@router.get("/catalog", response_model=Page[CatalogItem])
async def catalog(filters: Annotated[CatalogFilters, Query()], service: Service, _user: User) -> dict:
    """Return a globally sorted page of shared content."""
    return await service.catalog(filters.model_dump())


@router.get("/learning/summary", response_model=LearningSummary)
async def summary(service: Service, user: User) -> dict:
    """Return personal totals without team membership dependencies."""
    return await service.summary(user)


@router.get("/catalog/facets", response_model=Page[str])
async def facets(filters: Annotated[FacetFilters, Query()], service: Service, _user: User) -> dict:
    """Return searchable provider/category choices without their own selected filter."""
    return await service.facets(filters.model_dump())


@router.get("/learning/items", response_model=Page[LearningItem])
async def learning_items(filters: Annotated[LearningFilters, Query()], service: Service, user: User) -> dict:
    """Return one personal collection."""
    return await service.learning_items(user, filters.model_dump())


@router.get("/learning/paths/{path_id}", response_model=PathProgress)
async def path_progress(path_id: int, service: Service, user: User) -> dict:
    """Return a mixed path's course completion and independent selection."""
    return await service.path_progress(user, path_id)


@router.get("/activity", response_model=Page[ActivityEvent])
async def activity(filters: Annotated[ActivityFilters, Query()], service: Service, user: User) -> dict:
    """Return personal review updates or globally shared content events."""
    return await service.activity(user, filters.model_dump())
