"""Cookie transport adapter with session-bound CSRF and explicit header precedence."""

from __future__ import annotations

import hashlib
import hmac
from urllib.parse import urlsplit

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send

from backend.core.config import settings


COOKIE_NAME = "learning_session"


def csrf_token(token: str) -> str:
    """Derive a session-bound CSRF token without exposing the session credential."""
    return hmac.new(settings.browser_secret.encode(), token.encode(), hashlib.sha256).hexdigest()


def allowed_origin(request: Request) -> bool:
    """Match the configured origin (or a loopback development origin)."""
    origin = request.headers.get("origin", "").rstrip("/")
    if origin == settings.public_origin.rstrip("/"):
        return True
    parsed = urlsplit(origin)
    return settings.environment != "production" and parsed.scheme == "http" and parsed.hostname in {"localhost", "127.0.0.1"}


class BrowserSessionMiddleware:
    """Adapt cookies to legacy headers only after validating browser mutations."""

    def __init__(self, app: ASGIApp):
        """Retain the downstream application."""
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Validate origin/CSRF before passing cookie credentials to API handlers."""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request = Request(scope)
        token = request.cookies.get(COOKIE_NAME, "")
        has_header = "x-session-token" in request.headers
        mutation = request.method not in {"GET", "HEAD", "OPTIONS"}
        route_path = scope["path"].removeprefix(scope.get("root_path", ""))
        browser_login = route_path == "/auth/browser/login"
        if mutation and (browser_login or (token and not has_header)):
            valid_csrf = browser_login or hmac.compare_digest(request.headers.get("x-csrf-token", ""), csrf_token(token))
            if not allowed_origin(request) or not valid_csrf:
                await JSONResponse({"status": "error", "message": "csrf_rejected"}, status_code=403)(scope, receive, send)
                return
        if token and not has_header:
            scope = dict(scope)
            scope["headers"] = [*scope["headers"], (b"x-session-token", token.encode())]
        await self.app(scope, receive, send)
