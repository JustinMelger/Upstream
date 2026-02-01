from typing import List

from fastapi import APIRouter, Header, HTTPException

router = APIRouter(prefix="/paths", tags=["paths"])


@router.get("", response_model=List[dict])
def list_paths():
    from backend.services.paths_service import list_paths as fetch_paths

    return fetch_paths()


@router.get("/{path_id}", response_model=dict)
def get_path(path_id: int):
    from backend.services.paths_service import get_path as fetch_path

    path = fetch_path(path_id)
    return path or {"error": "not_found"}


@router.post("", response_model=dict)
def add_path(payload: dict, x_user_email: str | None = Header(default=None)):
    from backend.services.auth_service import is_admin
    from backend.services.paths_service import create_path

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


@router.delete("/{path_id}", response_model=dict)
def remove_path(path_id: int, x_user_email: str | None = Header(default=None)):
    from backend.services.auth_service import is_admin
    from backend.services.paths_service import delete_path

    if not is_admin(x_user_email):
        raise HTTPException(status_code=403, detail="admin_required")

    return {"deleted": delete_path(path_id)}
