from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import get_auth_service, get_courses_service, require_session
from backend.api.schemas import (
    CourseCreateRequest,
    CoursePayload,
    CourseUpdateRequest,
    DeleteCourseResponse,
)
from backend.services.auth_service import AuthService
from backend.services.courses_service import CoursesService


router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=List[CoursePayload])
async def list_courses(
    q: Optional[str] = Query(default=None, description="Search query"),
    provider: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    current_user: str = Depends(require_session),
    courses: CoursesService = Depends(get_courses_service),
):
    """List courses with optional filters.

    Args:
        q: Search query.
        provider: Provider filter.
        category: Category filter.
        level: Level filter.
        current_user: Authenticated username.

    Returns:
        list[dict]: Course list.
    """
    return await courses.list_courses(query=q, provider=provider, category=category, level=level)


@router.get("/{course_id}", response_model=CoursePayload)
async def get_course(
    course_id: int,
    current_user: str = Depends(require_session),
    courses: CoursesService = Depends(get_courses_service),
):
    """Get a single course by ID.

    Args:
        course_id: Course ID.
        current_user: Authenticated username.

    Returns:
        dict: Course payload.
    """
    course = await courses.get_course_by_id(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="not_found")
    return course


@router.post("", response_model=CoursePayload)
async def add_course(
    payload: CourseCreateRequest,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    courses: CoursesService = Depends(get_courses_service),
):
    """Create a course (admin only).

    Args:
        payload: Course payload.
        current_user: Authenticated username.

    Returns:
        dict: Created course.
    """
    if not await auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")
    return await courses.create_course(payload.model_dump())


@router.put("/{course_id}", response_model=CoursePayload)
async def edit_course(
    course_id: int,
    payload: CourseUpdateRequest,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    courses: CoursesService = Depends(get_courses_service),
):
    """Update a course (admin only).

    Args:
        course_id: Course ID.
        payload: Course updates.
        current_user: Authenticated username.

    Returns:
        dict: Updated course.
    """
    if not await auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")
    course = await courses.update_course(course_id, payload.model_dump())
    if not course:
        raise HTTPException(status_code=404, detail="not_found")
    return course


@router.delete("/{course_id}", response_model=DeleteCourseResponse)
async def remove_course(
    course_id: int,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    courses: CoursesService = Depends(get_courses_service),
):
    """Delete a course (admin only).

    Args:
        course_id: Course ID.
        current_user: Authenticated username.

    Returns:
        dict: Delete result.
    """
    if not await auth.is_admin(current_user):
        raise HTTPException(status_code=403, detail="admin_required")
    ok = await courses.delete_course(course_id)
    if not ok:
        raise HTTPException(status_code=404, detail="not_found")
    return {"deleted": ok}
