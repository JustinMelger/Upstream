from typing import List

from fastapi import APIRouter, Header, HTTPException, Query

from backend.services.auth_service import is_admin
from backend.services.paths_service import (
    create_path,
    delete_path,
    get_path as fetch_path,
    list_paths as fetch_paths,
    update_path,
)
from backend.services.user_paths_service import add_user_path, list_user_paths, remove_user_path


router = APIRouter(prefix="/paths", tags=["paths"])


@router.get("", response_model=List[dict])
def list_paths():
    return fetch_paths()


@router.post("", response_model=dict)
def add_path(payload: dict, x_user_email: str | None = Header(default=None)):
    if not is_admin(x_user_email):
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
def select_path(path_id: int, payload: dict):
    colleague_id = (payload.get("colleague_id") or "").strip()
    if not colleague_id:
        raise HTTPException(status_code=400, detail="missing_colleague_id")

    return add_user_path(colleague_id, path_id)


@router.post("/{path_id}/unselect", response_model=dict)
def unselect_path(path_id: int, payload: dict):
    colleague_id = (payload.get("colleague_id") or "").strip()
    if not colleague_id:
        raise HTTPException(status_code=400, detail="missing_colleague_id")

    removed = remove_user_path(colleague_id, path_id)
    return {"removed": removed}


@router.get("/selected/list", response_model=list[dict])
def list_selected_paths(colleague_id: str = Query(default="")):
    if not colleague_id:
        raise HTTPException(status_code=400, detail="missing_colleague_id")

    return list_user_paths(colleague_id)


@router.get("/{path_id}", response_model=dict)
def get_path(path_id: int):
    path = fetch_path(path_id)
    return path or {"error": "not_found"}


@router.delete("/{path_id}", response_model=dict)
def remove_path(path_id: int, x_user_email: str | None = Header(default=None)):
    if not is_admin(x_user_email):
        raise HTTPException(status_code=403, detail="admin_required")

    return {"deleted": delete_path(path_id)}


@router.put("/{path_id}", response_model=dict)
def edit_path(path_id: int, payload: dict, x_user_email: str | None = Header(default=None)):
    if not is_admin(x_user_email):
        raise HTTPException(status_code=403, detail="admin_required")

    try:
        return update_path(path_id, payload)
    except ValueError as exc:
        if str(exc) == "missing_name":
            raise HTTPException(status_code=400, detail="missing_name")
        if str(exc) == "duplicate_name":
            raise HTTPException(status_code=409, detail="duplicate_name")
        raise HTTPException(status_code=400, detail="invalid_request")
