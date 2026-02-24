from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.api.deps import (
    get_auth_service,
    get_course_recommendations_service,
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
    CourseRecommendationCreateRequest,
    CourseRecommendationPayload,
    CourseRecommendationSummaryItem,
    CourseReviewCreateRequest,
    CourseReviewPayload,
    CourseReviewSummaryItem,
    CourseUpdateRequest,
    DeleteCourseRecommendationResponse,
    DeleteCourseResponse,
    DeleteCourseReviewResponse,
)
from backend.services.auth_service import AuthService
from backend.services.course_recommendations_service import CourseRecommendationsService
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


@router.get("/recommendations/summary", response_model=list[CourseRecommendationSummaryItem])
async def course_recommendation_summaries(
    course_ids: List[int] = Query(default=[], description="Course IDs to summarize"),
    current_user: str = Depends(require_session),
    recommendations: CourseRecommendationsService = Depends(get_course_recommendations_service),
):
    """Return recommendation counts for each course id."""
    return await recommendations.summaries(course_ids=list(course_ids or []))


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
    await require_existing_owner_or_admin(
        row=await courses.get_course_by_id(course_id),
        current_user=current_user,
        auth=auth,
    )
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
    current_user: str = Depends(require_session),
    courses: CoursesService = Depends(get_courses_service),
    reviews: CourseReviewsService = Depends(get_course_reviews_service),
):
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
):
    """Create a review for a course (any authenticated user)."""
    require_row_exists(await courses.get_course_by_id(course_id))
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
    review = require_row_exists(await reviews.get_review_by_id(review_id=int(review_id)))
    require_row_parent_match(row=review, parent_field="course_id", parent_id=int(course_id))
    await require_existing_owner_or_admin(row=review, current_user=current_user, auth=auth)
    deleted = await reviews.delete_review(review_id=int(review_id))
    return {"deleted": bool(deleted)}


@router.get("/{course_id}/recommendations", response_model=list[CourseRecommendationPayload])
async def list_course_recommendations(
    course_id: int,
    current_user: str = Depends(require_session),
    courses: CoursesService = Depends(get_courses_service),
    recommendations: CourseRecommendationsService = Depends(get_course_recommendations_service),
):
    """List recommendations for a course."""
    require_row_exists(await courses.get_course_by_id(course_id))
    return await recommendations.list_recommendations(course_id=course_id)


@router.post("/{course_id}/recommendations", response_model=CourseRecommendationPayload)
async def create_course_recommendation(
    course_id: int,
    payload: CourseRecommendationCreateRequest,
    current_user: str = Depends(require_session),
    courses: CoursesService = Depends(get_courses_service),
    recommendations: CourseRecommendationsService = Depends(get_course_recommendations_service),
):
    """Create/update current user's recommendation for a course."""
    require_row_exists(await courses.get_course_by_id(course_id))
    return await recommendations.create_recommendation(
        course_id=course_id, payload=payload.model_dump(), created_by=current_user
    )


@router.delete("/{course_id}/recommendations/{recommendation_id}", response_model=DeleteCourseRecommendationResponse)
async def delete_course_recommendation(
    course_id: int,
    recommendation_id: int,
    current_user: str = Depends(require_session),
    auth: AuthService = Depends(get_auth_service),
    recommendations: CourseRecommendationsService = Depends(get_course_recommendations_service),
):
    """Delete a course recommendation (owner/admin only)."""
    recommendation = require_row_exists(
        await recommendations.get_recommendation_by_id(recommendation_id=int(recommendation_id))
    )
    require_row_parent_match(row=recommendation, parent_field="course_id", parent_id=int(course_id))
    await require_existing_owner_or_admin(row=recommendation, current_user=current_user, auth=auth)
    deleted = await recommendations.delete_recommendation(recommendation_id=int(recommendation_id))
    return {"deleted": bool(deleted)}
