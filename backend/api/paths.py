from typing import List

from fastapi import APIRouter

router = APIRouter(prefix="/paths", tags=["paths"])


@router.get("", response_model=List[dict])
def list_paths():
    return []


@router.get("/{path_id}", response_model=dict)
def get_path(path_id: int):
    return {"error": "not_found"}
