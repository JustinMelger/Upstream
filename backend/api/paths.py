from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import get_auth_service, get_paths_service, get_user_paths_service, require_session
from backend.services.auth_service import AuthService
from backend.services.paths_service import PathsService
from backend.services.user_paths_service import UserPathsService


router = APIRouter(prefix="/paths", tags=["paths"])


@router.get("", response_model=List[dict])
def list_paths(
    current_user: str = Depends(require_session),
    paths: PathsService = Depends(get_paths_service),
):
    """List all learning paths.

    Args:
        current_user: Authenticated username.

    Returns:
        list[dict]: Path list.
    """
    return paths.list_paths()


@router.post("", response_model=dict)
def add_path(
    payload: dict,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    paths: PathsService = Depends(get_paths_service),
):
    """Create a learning path (admin only).

    Args:
        payload: Path payload.
        current_user: Authenticated username.

    Returns:
        dict: Created path.
    """
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")

    try:
        return paths.create_path(payload)
    except ValueError as exc:
        if str(exc) == "missing_name":
            raise HTTPException(status_code=400, detail="missing_name")
        if str(exc) == "duplicate_name":
            raise HTTPException(status_code=409, detail="duplicate_name")
        raise HTTPException(status_code=400, detail="invalid_request")


@router.post("/{path_id}/select", response_model=dict)
def select_path(
    path_id: int,
    current_user: str = Depends(require_session),
    user_paths: UserPathsService = Depends(get_user_paths_service),
):
    """Add a path to the current user's selections.

    Args:
        path_id: Path ID.
        current_user: Authenticated username.

    Returns:
        dict: Selection result.
    """
    return user_paths.add_user_path(current_user, path_id)


@router.post("/{path_id}/unselect", response_model=dict)
def unselect_path(
    path_id: int,
    current_user: str = Depends(require_session),
    user_paths: UserPathsService = Depends(get_user_paths_service),
):
    """Remove a path from the current user's selections.

    Args:
        path_id: Path ID.
        current_user: Authenticated username.

    Returns:
        dict: Removal result.
    """
    removed = user_paths.remove_user_path(current_user, path_id)
    return {"removed": removed}


@router.post("/{path_id}/status", response_model=dict)
def set_path_status(
    path_id: int,
    payload: dict,
    current_user: str = Depends(require_session),
    user_paths: UserPathsService = Depends(get_user_paths_service),
):
    """Update the status for a selected path.

    Args:
        path_id: Path ID.
        payload: Status payload.
        current_user: Authenticated username.

    Returns:
        dict: Update result.
    """
    status = (payload.get("status") or "").strip()
    if not status:
        raise HTTPException(status_code=400, detail="missing_fields")

    try:
        updated = user_paths.update_user_path_status(current_user, path_id, status)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_status")

    if updated == 0:
        raise HTTPException(status_code=404, detail="path_not_selected")

    return {"updated": updated}


@router.get("/selected/list", response_model=list[dict])
def list_selected_paths(
    current_user: str = Depends(require_session),
    user_paths: UserPathsService = Depends(get_user_paths_service),
):
    """List paths selected by the current user.

    Args:
        current_user: Authenticated username.

    Returns:
        list[dict]: Selected paths.
    """
    return user_paths.list_user_paths(current_user)


@router.get("/{path_id}", response_model=dict)
def get_path(
    path_id: int,
    current_user: str = Depends(require_session),
    paths: PathsService = Depends(get_paths_service),
):
    """Get a learning path by ID.

    Args:
        path_id: Path ID.
        current_user: Authenticated username.

    Returns:
        dict: Path payload or not_found.
    """
    path = paths.get_path(path_id)
    return path or {"error": "not_found"}


@router.delete("/{path_id}", response_model=dict)
def remove_path(
    path_id: int,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    paths: PathsService = Depends(get_paths_service),
):
    """Delete a learning path (admin only).

    Args:
        path_id: Path ID.
        current_user: Authenticated username.

    Returns:
        dict: Delete result.
    """
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")

    return {"deleted": paths.delete_path(path_id)}


@router.put("/{path_id}", response_model=dict)
def edit_path(
    path_id: int,
    payload: dict,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    paths: PathsService = Depends(get_paths_service),
):
    """Update a learning path (admin only).

    Args:
        path_id: Path ID.
        payload: Path updates.
        current_user: Authenticated username.

    Returns:
        dict: Updated path.
    """
    if not auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")

    try:
        return paths.update_path(path_id, payload)
    except ValueError as exc:
        if str(exc) == "missing_name":
            raise HTTPException(status_code=400, detail="missing_name")
        if str(exc) == "duplicate_name":
            raise HTTPException(status_code=409, detail="duplicate_name")
        raise HTTPException(status_code=400, detail="invalid_request")
