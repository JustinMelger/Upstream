from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.async_repositories.articles import ArticlesRepository as SQLArticlesRepository
from backend.database.async_repositories.auth import AuthRepository as SQLAuthRepository
from backend.database.async_repositories.course_reviews import CourseReviewsRepository as SQLCourseReviewsRepository
from backend.database.async_repositories.courses import CoursesRepository as SQLCoursesRepository
from backend.database.async_repositories.paths import PathsRepository as SQLPathsRepository
from backend.database.async_repositories.tracking import TrackingRepository as SQLTrackingRepository
from backend.database.async_repositories.user_paths import UserPathsRepository as SQLUserPathsRepository
from backend.database.session import get_session
from backend.services.articles_service import ArticlesService
from backend.services.auth_service import AuthService
from backend.services.course_reviews_service import CourseReviewsService
from backend.services.courses_service import CoursesService
from backend.services.paths_service import PathsService
from backend.services.tracking_service import TrackingService
from backend.services.user_paths_service import UserPathsService


async def get_auth_service(session: AsyncSession = Depends(get_session)) -> AuthService:
    """Provide a request-scoped AuthService dependency."""
    return AuthService(SQLAuthRepository(session))


async def get_courses_service(session: AsyncSession = Depends(get_session)) -> CoursesService:
    """Provide a request-scoped CoursesService dependency."""
    return CoursesService(SQLCoursesRepository(session))


async def get_paths_service(session: AsyncSession = Depends(get_session)) -> PathsService:
    """Provide a request-scoped PathsService dependency."""
    return PathsService(SQLPathsRepository(session))


async def get_user_paths_service(session: AsyncSession = Depends(get_session)) -> UserPathsService:
    """Provide a request-scoped UserPathsService dependency."""
    return UserPathsService(SQLUserPathsRepository(session))


async def get_tracking_service(session: AsyncSession = Depends(get_session)) -> TrackingService:
    """Provide a request-scoped TrackingService dependency."""
    return TrackingService(SQLTrackingRepository(session))


async def get_articles_service(session: AsyncSession = Depends(get_session)) -> ArticlesService:
    """Provide a request-scoped ArticlesService dependency."""
    return ArticlesService(SQLArticlesRepository(session))


async def get_course_reviews_service(session: AsyncSession = Depends(get_session)) -> CourseReviewsService:
    """Provide a request-scoped CourseReviewsService dependency."""
    return CourseReviewsService(SQLCourseReviewsRepository(session))


async def require_session(
    x_session_token: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),
) -> str:
    """Validate session token and return the authenticated username."""
    session = await auth.get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    return str(session["colleague_id"])
