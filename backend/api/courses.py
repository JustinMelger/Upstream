from typing import List, Optional

from fastapi import APIRouter, Header, HTTPException, Query

from backend.services.auth_service import is_admin
from backend.services.courses_service import (
    create_course,
    delete_course,
    get_course_by_id,
    list_courses as fetch_courses,
    update_course,
)


router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=List[dict])
def list_courses(
    q: Optional[str] = Query(default=None, description="Search query"),
    provider: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
):
    return fetch_courses(query=q, provider=provider, category=category, level=level)


@router.get("/{course_id}", response_model=dict)
def get_course(course_id: int):
    course = get_course_by_id(course_id)
    return course or {"error": "not_found"}


@router.post("", response_model=dict)
def add_course(payload: dict, x_user_email: str | None = Header(default=None)):
    if not is_admin(x_user_email):
        raise HTTPException(status_code=403, detail="admin_required")
    try:
        return create_course(payload)
    except ValueError:
        raise HTTPException(status_code=400, detail="missing_title")


@router.put("/{course_id}", response_model=dict)
def edit_course(course_id: int, payload: dict, x_user_email: str | None = Header(default=None)):
    if not is_admin(x_user_email):
        raise HTTPException(status_code=403, detail="admin_required")
    course = update_course(course_id, payload)
    if not course:
        return {"error": "not_found"}
    return course


@router.delete("/{course_id}", response_model=dict)
def remove_course(course_id: int, x_user_email: str | None = Header(default=None)):
    if not is_admin(x_user_email):
        raise HTTPException(status_code=403, detail="admin_required")
    ok = delete_course(course_id)
    return {"deleted": ok}
