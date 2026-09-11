"""Browser authentication keeps credentials out of JavaScript."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Response
from pydantic import BaseModel

from backend.api.auth import login
from backend.api.deps import get_auth_service
from backend.api.schemas.auth import LoginRequest
from backend.core.browser_security import COOKIE_NAME, csrf_token
from backend.core.config import settings
from backend.services.auth_service import AuthService


router = APIRouter(prefix="/auth/browser", tags=["browser-auth"])


class BrowserSession(BaseModel):
    """Public session metadata and a non-credential mutation token."""

    username: str
    role: str
    expires_at: str
    csrf_token: str


@router.post("/login", response_model=BrowserSession)
async def browser_login(payload: LoginRequest, response: Response, auth: AuthService = Depends(get_auth_service)) -> dict:
    """Create a browser session using the same credential rules as header login."""
    result = await login(payload, auth)
    token = str(result["token"])
    response.set_cookie(
        COOKIE_NAME,
        token,
        httponly=True,
        secure=settings.environment == "production",
        samesite="lax",
        max_age=settings.session_days * 86400,
        path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return {key: result[key] for key in ("username", "role", "expires_at")} | {"csrf_token": csrf_token(token)}


@router.get("/session", response_model=BrowserSession)
async def browser_session(
    response: Response, x_session_token: str | None = Header(default=None), auth: AuthService = Depends(get_auth_service)
) -> dict:
    """Recover a browser session after reload without returning its credential."""
    session = await auth.get_session(x_session_token)
    if not session:
        raise HTTPException(401, "unauthorized")
    user = await auth.get_user(session["colleague_id"])
    if not user or user.disabled:
        raise HTTPException(401, "unauthorized")
    response.headers["Cache-Control"] = "no-store"
    return {
        "username": user.username,
        "role": user.role,
        "expires_at": session["expires_at"],
        "csrf_token": csrf_token(x_session_token or ""),
    }


@router.post("/logout")
async def browser_logout(
    response: Response, x_session_token: str | None = Header(default=None), auth: AuthService = Depends(get_auth_service)
) -> dict[str, bool]:
    """Revoke the current browser session and clear its cookie."""
    await auth.revoke_session(x_session_token)
    response.delete_cookie(COOKIE_NAME, path="/", secure=settings.environment == "production", httponly=True, samesite="lax")
    response.headers["Cache-Control"] = "no-store"
    return {"logged_out": True}
