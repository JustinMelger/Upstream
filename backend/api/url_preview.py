from typing import Any

from fastapi import APIRouter, Depends

from backend.api.deps import get_url_preview_service, require_session
from backend.api.schemas import UrlPreviewMetadataRequest, UrlPreviewMetadataResponse
from backend.services.url_preview_service import UrlPreviewService


router = APIRouter(prefix="/url-preview", tags=["url-preview"])


@router.post("/metadata", response_model=UrlPreviewMetadataResponse)
async def resolve_url_metadata(
    payload: UrlPreviewMetadataRequest,
    _current_user: str = Depends(require_session),
    previews: UrlPreviewService = Depends(get_url_preview_service),
) -> dict[str, Any]:
    """Resolve URL metadata and autofill suggestions for share dialogs."""
    return await previews.resolve_metadata(source_url=str(payload.url or ""))
