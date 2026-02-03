from typing import List

from fastapi import APIRouter, Depends, HTTPException

from backend.api.deps import require_session
from backend.services.auth_service import is_admin
from backend.services.paths_service import (
    create_path,
    delete_path,
    get_path as fetch_path,
    list_paths as fetch_paths,
    update_path,
)
from backend.services.user_paths_service import add_user_path, list_user_paths, remove_user_path, update_user_path_status


router = APIRouter(prefix="/paths", tags=["paths"])


@router.get("", response_model=List[dict])
def list_paths(current_user: str = Depends(require_session)):
    return fetch_paths()


@router.post("", response_model=dict)
def add_path(payload: dict, current_user: str = Depends(require_session)):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")

    try:
        return create_path(payload)
    except ValueError as exc:
        if str(exc) == "missing_name":
            raise HTTPException(status_code=400, detail="missing_name")
        if str(exc) == "duplicate_name":
            raise HTTPException(status_code=409, detail="duplicate_name")
        raise HTTPException(status_code=400, detail="invalid_request")


@router.post("/{path_id}/select", response_model=dict)
def select_path(path_id: int, current_user: str = Depends(require_session)):
    return add_user_path(current_user, path_id)


@router.post("/{path_id}/unselect", response_model=dict)
def unselect_path(path_id: int, current_user: str = Depends(require_session)):
    removed = remove_user_path(current_user, path_id)
    return {"removed": removed}


@router.post("/{path_id}/status", response_model=dict)
def set_path_status(path_id: int, payload: dict, current_user: str = Depends(require_session)):
    status = (payload.get("status") or "").strip()
    if not status:
        raise HTTPException(status_code=400, detail="missing_fields")

    try:
        updated = update_user_path_status(current_user, path_id, status)
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid_status")

    if updated == 0:
        raise HTTPException(status_code=404, detail="path_not_selected")

    return {"updated": updated}


@router.get("/selected/list", response_model=list[dict])
def list_selected_paths(current_user: str = Depends(require_session)):
    return list_user_paths(current_user)


@router.get("/{path_id}", response_model=dict)
def get_path(path_id: int, current_user: str = Depends(require_session)):
    path = fetch_path(path_id)
    return path or {"error": "not_found"}


@router.delete("/{path_id}", response_model=dict)
def remove_path(path_id: int, current_user: str = Depends(require_session)):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")

    return {"deleted": delete_path(path_id)}


@router.put("/{path_id}", response_model=dict)
def edit_path(path_id: int, payload: dict, current_user: str = Depends(require_session)):
    if not is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")

    try:
        return update_path(path_id, payload)
    except ValueError as exc:
        if str(exc) == "missing_name":
            raise HTTPException(status_code=400, detail="missing_name")
        if str(exc) == "duplicate_name":
            raise HTTPException(status_code=409, detail="duplicate_name")
        raise HTTPException(status_code=400, detail="invalid_request")
