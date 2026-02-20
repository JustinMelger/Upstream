"""Error handling utilities for the NiceGUI frontend.

The backend uses a consistent domain error pattern (`ServiceError` subclasses)
and converts failures into a standard error envelope.

In the frontend, we aim for a similar outcome:

- Keep errors as typed exceptions (`ApiError`, `FrontendError`).
- Centralize mapping to user-facing notifications.
- Avoid duplicating `try/except ui.notify(...)` blocks across pages.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Any, Awaitable, Callable, cast, TypeVar

from nicegui import ui

from frontend.ui.nicegui.core.api_client import ApiError


logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class FrontendError(Exception):
    """Represents a frontend-domain failure (not necessarily an API failure).

    Attributes:
        status_code: Similar to backend `ServiceError.status_code`. Use 500 for
            generic errors; use 400/401/etc. when appropriate.
        message: Human-friendly error message.
        context: Optional dict for structured logging.
    """

    status_code: int
    message: str
    context: dict[str, Any] | None = None

    def __str__(self) -> str:
        return f"{self.status_code}: {self.message}"


def _message_for_exception(exc: Exception) -> str:
    """Convert an exception into a user-facing message."""
    if isinstance(exc, ApiError):
        return str(exc)
    if isinstance(exc, FrontendError):
        return str(exc)
    return str(exc) or "Unexpected error"


def safe_notify(message: str, *, type: str = "info") -> None:  # noqa: A002
    """Best-effort UI notification that tolerates missing/deleted UI context."""
    try:
        ui.notify(message, type=type)
    except Exception:
        logger.warning("Unable to show notification; UI context is no longer available")


def notify_error(exc: Exception, *, title: str | None = None) -> None:
    """Show an error notification for an exception.

    Args:
        exc: Exception to present.
        title: Optional prefix to provide context (e.g. "Login failed").
    """
    msg = _message_for_exception(exc)
    text = f"{title}: {msg}" if title else msg
    safe_notify(text, type="negative")


def guard_ui_action(
    *,
    title: str | None = None,
    log_message: str | None = None,
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Decorator for async UI event handlers to standardize error handling.

    This keeps exceptions from bubbling into NiceGUI's 500 error pages and
    ensures a consistent user-facing notification.

    Args:
        title: Optional prefix for the toast notification.
        log_message: Optional log message to use when logging unexpected errors.

    Returns:
        Decorator that wraps an async function.
    """

    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            try:
                return await func(*args, **kwargs)
            except (ApiError, FrontendError) as exc:
                notify_error(cast(Exception, exc), title=title)
                return cast(T, None)
            except Exception as exc:
                # Log unexpected errors with a stack trace but keep the UI alive.
                logger.exception(log_message or f"{func.__name__} failed", exc_info=exc)
                notify_error(exc, title=title or "Unexpected error")
                return cast(T, None)

        return wrapper

    return decorator
