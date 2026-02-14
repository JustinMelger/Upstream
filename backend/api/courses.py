from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import get_auth_service, get_course_reviews_service, get_courses_service, require_session
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


@router.get("/reviews/summary", response_model=list[CourseReviewSummaryItem])
async def course_review_summaries(
    course_ids: List[int] = Query(default=[], description="Course IDs to summarize"),
    current_user: str = Depends(require_session),
    reviews: CourseReviewsService = Depends(get_course_reviews_service),
):
    """Return average rating + count for each course id."""
    return await reviews.summaries(course_ids=list(course_ids or []))


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
    courses: CoursesService = Depends(get_courses_service),
):
    """Create a course (any authenticated user).

    Args:
        payload: Course payload.
        current_user: Authenticated username.

    Returns:
        dict: Created course.
    """
    data = payload.model_dump()
    data["created_by"] = current_user
    return await courses.create_course(data)


@router.put("/{course_id}", response_model=CoursePayload)
async def edit_course(
    course_id: int,
    payload: CourseUpdateRequest,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    courses: CoursesService = Depends(get_courses_service),
):
    """Update a course (owner/admin only).

    Args:
        course_id: Course ID.
        payload: Course updates.
        current_user: Authenticated username.

    Returns:
        dict: Updated course.
    """
    if not await auth.is_admin(current_user):
        existing = await courses.get_course_by_id(course_id)
        if not existing:
            raise HTTPException(status_code=404, detail="not_found")
        if str(existing.get("created_by") or "") != str(current_user):
            raise HTTPException(status_code=403, detail="forbidden")
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
    """Delete a course (owner/admin only).

    Args:
        course_id: Course ID.
        current_user: Authenticated username.

    Returns:
        dict: Delete result.
    """
    if not await auth.is_admin(current_user):
        existing = await courses.get_course_by_id(course_id)
        if not existing:
            raise HTTPException(status_code=404, detail="not_found")
        if str(existing.get("created_by") or "") != str(current_user):
            raise HTTPException(status_code=403, detail="forbidden")
    ok = await courses.delete_course(course_id)
    if not ok:
        raise HTTPException(status_code=404, detail="not_found")
    return {"deleted": ok}


@router.get("/{course_id}/reviews", response_model=list[CourseReviewPayload])
async def list_course_reviews(
    course_id: int,
    current_user: str = Depends(require_session),
    courses: CoursesService = Depends(get_courses_service),
    reviews: CourseReviewsService = Depends(get_course_reviews_service),
):
    """List reviews for a course."""
    existing = await courses.get_course_by_id(course_id)
    if not existing:
        raise HTTPException(status_code=404, detail="not_found")
    return await reviews.list_reviews(course_id=course_id)


@router.post("/{course_id}/reviews", response_model=CourseReviewPayload)
async def create_course_review(
    course_id: int,
    payload: CourseReviewCreateRequest,
    current_user: str = Depends(require_session),
    courses: CoursesService = Depends(get_courses_service),
    reviews: CourseReviewsService = Depends(get_course_reviews_service),
):
    """Create a review for a course (any authenticated user)."""
    existing = await courses.get_course_by_id(course_id)
    if not existing:
        raise HTTPException(status_code=404, detail="not_found")
    return await reviews.create_review(course_id=course_id, payload=payload.model_dump(), created_by=current_user)


@router.delete("/{course_id}/reviews/{review_id}", response_model=DeleteCourseReviewResponse)
async def delete_course_review(
    course_id: int,
    review_id: int,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    reviews: CourseReviewsService = Depends(get_course_reviews_service),
):
    """Delete a course review (owner/admin only)."""
    review = await reviews.get_review_by_id(review_id=int(review_id))
    if not review:
        raise HTTPException(status_code=404, detail="not_found")
    if int(review.get("course_id") or 0) != int(course_id):
        raise HTTPException(status_code=404, detail="not_found")
    if not await auth.is_admin(current_user) and str(review.get("created_by") or "") != str(current_user):
        raise HTTPException(status_code=403, detail="forbidden")
    deleted = await reviews.delete_review(review_id=int(review_id))
    return {"deleted": bool(deleted)}
