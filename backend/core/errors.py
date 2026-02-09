from __future__ import annotations

from datetime import datetime, timezone
from functools import wraps
import inspect
import logging
from typing import Any, Callable, TypeVar

from fastapi import HTTPException


logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class ServiceError(HTTPException):
    """Base FastAPI exception for service-domain failures."""

    def __init__(self, *, detail: str, status_code: int = 500) -> None:
        """Initialize the service error.

        Args:
            detail: Human-readable error message or error code.
            status_code: HTTP status code.
        """
        super().__init__(status_code=status_code, detail=detail)


class AuthServiceError(ServiceError):
    """Base FastAPI exception for auth domain failures."""

    def __init__(self, *, detail: str, status_code: int = 500) -> None:
        """Initialize the auth service error.

        Args:
            detail: Human-readable error message or error code.
            status_code: HTTP status code.
        """
        super().__init__(status_code=status_code, detail=detail)


class CoursesServiceError(ServiceError):
    """Base FastAPI exception for courses domain failures."""

    def __init__(self, *, detail: str, status_code: int = 500) -> None:
        """Initialize the courses service error.

        Args:
            detail: Human-readable error message or error code.
            status_code: HTTP status code.
        """
        super().__init__(status_code=status_code, detail=detail)


class PathsServiceError(ServiceError):
    """Base FastAPI exception for paths domain failures."""

    def __init__(self, *, detail: str, status_code: int = 500) -> None:
        """Initialize the paths service error.

        Args:
            detail: Human-readable error message or error code.
            status_code: HTTP status code.
        """
        super().__init__(status_code=status_code, detail=detail)


class UserPathsServiceError(ServiceError):
    """Base FastAPI exception for user-paths domain failures."""

    def __init__(self, *, detail: str, status_code: int = 500) -> None:
        """Initialize the user-paths service error.

        Args:
            detail: Human-readable error message or error code.
            status_code: HTTP status code.
        """
        super().__init__(status_code=status_code, detail=detail)


class TrackingServiceError(ServiceError):
    """Base FastAPI exception for tracking domain failures."""

    def __init__(self, *, detail: str, status_code: int = 500) -> None:
        """Initialize the tracking service error.

        Args:
            detail: Human-readable error message or error code.
            status_code: HTTP status code.
        """
        super().__init__(status_code=status_code, detail=detail)


def _error_content(message: str) -> dict[str, str]:
    """Build a standard error envelope payload.

    Args:
        message: Error message.

    Returns:
        JSON-serializable error payload.
    """
    return {
        "status": "error",
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def format_service_error(exc: HTTPException) -> dict[str, str]:
    """Convert a service-domain exception into a standard JSON error payload.

    Args:
        exc: Domain HTTPException.

    Returns:
        Error payload with message and timestamp.
    """
    return _error_content(str(exc.detail))


def error_handler(
    *,
    service_error: type[ServiceError],
    message: str,
    status_code: int = 500,
    log_message: str | None = None,
) -> Callable[[F], F]:
    """Decorator that converts uncaught exceptions into a domain ServiceError.

    Notes:
        - Re-raises HTTPException unchanged so endpoint semantics are preserved.
    """

    def decorator(func: F) -> F:
        """Wrap a function and convert uncaught errors into a domain ServiceError."""
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def wrapper(*args, **kwargs):
                """Async wrapper that preserves HTTPException and wraps other exceptions."""
                try:
                    return await func(*args, **kwargs)
                except HTTPException:
                    raise
                except Exception as exc:
                    logger.error(log_message or f"{service_error.__name__} raised", exc_info=exc)
                    raise service_error(detail=message, status_code=status_code)

        else:

            @wraps(func)
            def wrapper(*args, **kwargs):
                """Sync wrapper that preserves HTTPException and wraps other exceptions."""
                try:
                    return func(*args, **kwargs)
                except HTTPException:
                    raise
                except Exception as exc:
                    logger.error(log_message or f"{service_error.__name__} raised", exc_info=exc)
                    raise service_error(detail=message, status_code=status_code)

        return wrapper  # type: ignore[return-value]

    return decorator


def auth_error_handler(
    message: str = "An unexpected error occurred while handling authentication",
    status_code: int = 500,
) -> Callable[[F], F]:
    """Backwards-compatible wrapper around error_handler for the auth domain."""

    return error_handler(
        service_error=AuthServiceError,
        message=message,
        status_code=status_code,
        log_message="Auth service error",
    )


def courses_error_handler(
    message: str = "An unexpected error occurred while handling courses",
    status_code: int = 500,
) -> Callable[[F], F]:
    """Backwards-compatible wrapper around error_handler for the courses domain."""

    return error_handler(
        service_error=CoursesServiceError,
        message=message,
        status_code=status_code,
        log_message="Courses service error",
    )


def paths_error_handler(
    message: str = "An unexpected error occurred while handling learning paths",
    status_code: int = 500,
) -> Callable[[F], F]:
    """Backwards-compatible wrapper around error_handler for the paths domain."""

    return error_handler(
        service_error=PathsServiceError,
        message=message,
        status_code=status_code,
        log_message="Paths service error",
    )


def user_paths_error_handler(
    message: str = "An unexpected error occurred while handling selected paths",
    status_code: int = 500,
) -> Callable[[F], F]:
    """Backwards-compatible wrapper around error_handler for the user-paths domain."""

    return error_handler(
        service_error=UserPathsServiceError,
        message=message,
        status_code=status_code,
        log_message="User paths service error",
    )


def tracking_error_handler(
    message: str = "An unexpected error occurred while handling tracking",
    status_code: int = 500,
) -> Callable[[F], F]:
    """Backwards-compatible wrapper around error_handler for the tracking domain."""

    return error_handler(
        service_error=TrackingServiceError,
        message=message,
        status_code=status_code,
        log_message="Tracking service error",
    )
