from fastapi import Depends, Header, HTTPException

from backend.services.auth_service import auth_service, AuthService
from backend.services.courses_service import courses_service, CoursesService
from backend.services.paths_service import paths_service, PathsService
from backend.services.user_paths_service import user_paths_service, UserPathsService


def get_auth_service() -> AuthService:
    """Provide the AuthService dependency.

    Returns:
        AuthService: Shared auth service instance.
    """
    return auth_service


def get_courses_service() -> CoursesService:
    """Provide the CoursesService dependency.

    Returns:
        CoursesService: Shared courses service instance.
    """
    return courses_service


def get_paths_service() -> PathsService:
    """Provide the PathsService dependency.

    Returns:
        PathsService: Shared paths service instance.
    """
    return paths_service


def get_user_paths_service() -> UserPathsService:
    """Provide the UserPathsService dependency.

    Returns:
        UserPathsService: Shared user paths service instance.
    """
    return user_paths_service


def require_session(
    x_session_token: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),
) -> str:
    """Validate session token and return the authenticated username.

    Args:
        x_session_token: Session token from request headers.
        auth: Auth service dependency.

    Returns:
        Authenticated username.

    Raises:
        HTTPException: If the session is missing or invalid.
    """
    session = auth.get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    return session["colleague_id"]
