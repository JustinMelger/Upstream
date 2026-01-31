from typing import List, Optional

from fastapi import APIRouter, Query

from backend.services.courses_service import list_courses as fetch_courses

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
    courses = fetch_courses()
    for course in courses:
        if course["id"] == course_id:
            return course
    return {"error": "not_found"}
