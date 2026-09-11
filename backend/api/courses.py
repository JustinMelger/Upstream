from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import (
    get_auth_service,
    get_course_reviews_service,
    get_courses_service,
    require_session,
)
from backend.api.policies import (
    require_existing_owner_or_admin,
    require_row_exists,
    require_row_parent_match,
)
from backend.api.schemas import (
    CourseCreateRequest,
    CoursePayload,
    CourseReviewCreateRequest,
    CourseReviewPayload,
    CourseReviewSummaryItem,
    CourseUpdateRequest,
    DeleteCourseResponse,
    DeleteCourseReviewResponse,
)
from backend.services.auth_service import AuthService
from backend.services.course_reviews_service import CourseReviewsService
from backend.services.courses_service import CoursesService


router = APIRouter(prefix="/courses", tags=["courses"])


@router.get("", response_model=List[CoursePayload])
async def list_courses(
    q: Optional[str] = Query(default=None, description="Search query"),
    provider: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    _current_user: str = Depends(require_session),
    courses: CoursesService = Depends(get_courses_service),
) -> list[dict[str, Any]]:
    """List courses with optional filters.

    Args:
        q: Search query.
        provider: Provider filter.
        category: Category filter.
        level: Level filter.
        _current_user: Authenticated username.

    Returns:
        list[dict]: Course list.
    """
    return await courses.list_courses(query=q, provider=provider, category=category, level=level)


@router.get("/reviews/summary", response_model=list[CourseReviewSummaryItem])
async def course_review_summaries(
    course_ids: List[int] = Query(default=[], description="Course IDs to summarize"),
    _current_user: str = Depends(require_session),
    reviews: CourseReviewsService = Depends(get_course_reviews_service),
) -> list[dict[str, Any]]:
    """Return average rating + count for each course id."""
    return await reviews.summaries(course_ids=list(course_ids or []))


@router.get("/{course_id}", response_model=CoursePayload)
async def get_course(
    course_id: int,
    _current_user: str = Depends(require_session),
    courses: CoursesService = Depends(get_courses_service),
) -> dict[str, Any]:
    """Get a single course by ID.

    Args:
        course_id: Course ID.
        _current_user: Authenticated username.

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
    courses: CoursesService = Depends(get_courses_service),
) -> dict[str, Any]:
    """Create a course (any authenticated user).

    Args:
        payload: Course payload.
        current_user: Authenticated username.

    Returns:
        dict: Created course.
    """
    data = payload.model_dump(exclude_unset=True)
    data["created_by"] = current_user
    return await courses.create_course(data)


@router.put("/{course_id}", response_model=CoursePayload)
async def edit_course(
    course_id: int,
    payload: CourseUpdateRequest,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    courses: CoursesService = Depends(get_courses_service),
) -> dict[str, Any]:
    """Update a course (owner/admin only).

    Args:
        course_id: Course ID.
        payload: Course updates.
        current_user: Authenticated username.

    Returns:
        dict: Updated course.
    """
    await require_existing_owner_or_admin(
        row=await courses.get_course_by_id(course_id),
        current_user=current_user,
        auth=auth,
    )
    course = await courses.update_course(course_id, payload.model_dump(exclude_unset=True))
    if not course:
        raise HTTPException(status_code=404, detail="not_found")
    return course


@router.delete("/{course_id}", response_model=DeleteCourseResponse)
async def remove_course(
    course_id: int,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    courses: CoursesService = Depends(get_courses_service),
) -> dict[str, bool]:
    """Delete a course (owner/admin only).

    Args:
        course_id: Course ID.
        current_user: Authenticated username.

    Returns:
        dict: Delete result.
    """
    await require_existing_owner_or_admin(
        row=await courses.get_course_by_id(course_id),
        current_user=current_user,
        auth=auth,
    )
    ok = await courses.delete_course(course_id)
    if not ok:
        raise HTTPException(status_code=404, detail="not_found")
    return {"deleted": ok}


@router.get("/{course_id}/reviews", response_model=list[CourseReviewPayload])
async def list_course_reviews(
    course_id: int,
    _current_user: str = Depends(require_session),
    courses: CoursesService = Depends(get_courses_service),
    reviews: CourseReviewsService = Depends(get_course_reviews_service),
) -> list[dict[str, Any]]:
    """List reviews for a course."""
    require_row_exists(await courses.get_course_by_id(course_id))
    return await reviews.list_reviews(course_id=course_id)


@router.post("/{course_id}/reviews", response_model=CourseReviewPayload)
async def create_course_review(
    course_id: int,
    payload: CourseReviewCreateRequest,
    current_user: str = Depends(require_session),
    courses: CoursesService = Depends(get_courses_service),
    reviews: CourseReviewsService = Depends(get_course_reviews_service),
) -> dict[str, Any]:
    """Create a review for a course (any authenticated user)."""
    require_row_exists(await courses.get_course_by_id(course_id))
    return await reviews.create_review(
        course_id=course_id, payload=payload.model_dump(exclude_unset=True), created_by=current_user
    )


@router.delete("/{course_id}/reviews/{review_id}", response_model=DeleteCourseReviewResponse)
async def delete_course_review(
    course_id: int,
    review_id: int,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    reviews: CourseReviewsService = Depends(get_course_reviews_service),
) -> dict[str, bool]:
    """Delete a course review (owner/admin only)."""
    review = require_row_exists(await reviews.get_review_by_id(review_id=int(review_id)))
    require_row_parent_match(row=review, parent_field="course_id", parent_id=int(course_id))
    await require_existing_owner_or_admin(row=review, current_user=current_user, auth=auth)
    deleted = await reviews.delete_review(review_id=int(review_id))
    return {"deleted": bool(deleted)}
