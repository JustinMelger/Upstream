from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException

from backend.api.deps import get_auth_service, require_account_admin, require_admin, require_session
from backend.api.schemas import (
    ChangePasswordRequest,
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserResponse,
    DisableUserRequest,
    DisableUserResponse,
    LoginRequest,
    LoginResponse,
    LogoutResponse,
    MeResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    RoleResponse,
    UserListItem,
)
from backend.api.schemas.auth import UpdateRoleRequest, UpdateRoleResponse
from backend.core.config import settings
from backend.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(payload: LoginRequest, auth: AuthService = Depends(get_auth_service)) -> dict[str, Any]:
    """Authenticate a user and create a session.

    Args:
        payload: Login payload with username and password.

    Returns:
        dict: Session token, expiry, and user metadata.

    Raises:
        HTTPException: If credentials are invalid.
    """
    username = payload.username
    password = payload.password

    await auth.purge_expired_sessions()

    if not await auth.has_users():
        if username != settings.bootstrap_admin_username or password != settings.bootstrap_admin_password:
            raise HTTPException(status_code=401, detail="invalid_credentials")
        created_user = await auth.create_user(username, password, "admin")
        session = await auth.create_session(username)
        return {
            "token": session["token"],
            "expires_at": session["expires_at"],
            "username": created_user["username"],
            "role": created_user["role"],
            "bootstrap": True,
        }

    authenticated_user = await auth.authenticate_user(username, password)
    if not authenticated_user:
        raise HTTPException(status_code=401, detail="invalid_credentials")

    session = await auth.create_session(str(authenticated_user["username"] or ""))
    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "username": authenticated_user["username"],
        "role": authenticated_user["role"],
    }


@router.get("/me", response_model=MeResponse)
async def me(
    x_session_token: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),
) -> dict[str, Any]:
    """Return the current authenticated user.

    Args:
        x_session_token: Session token from request headers.

    Returns:
        dict: User metadata and session expiry.
    """
    session = await auth.get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    username = session["colleague_id"]
    user = await auth.get_user(username)
    if not user:
        raise HTTPException(status_code=401, detail="unauthorized")
    return {"username": user.username, "role": user.role, "expires_at": session["expires_at"]}


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    x_session_token: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),
) -> dict[str, int]:
    """Revoke all sessions for the current user.

    Args:
        x_session_token: Session token from request headers.

    Returns:
        dict: Number of revoked sessions.
    """
    session = await auth.get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    revoked = await auth.revoke_session(x_session_token)
    return {"revoked": revoked}


@router.get("/role", response_model=RoleResponse)
async def get_role(
    x_session_token: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),
) -> dict[str, str]:
    """Return the role for the current user.

    Args:
        x_session_token: Session token from request headers.

    Returns:
        dict: Role name.
    """
    session = await auth.get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    user = await auth.get_user(session["colleague_id"])
    if not user:
        raise HTTPException(status_code=401, detail="unauthorized")
    return {"role": user.role}


@router.post("/password/change", response_model=ResetPasswordResponse)
async def change_password_endpoint(
    payload: ChangePasswordRequest,
    auth: AuthService = Depends(get_auth_service),
    current_user: str = Depends(require_session),
) -> dict[str, int]:
    """Change the authenticated user's password.

    Args:
        payload: Current and replacement password.
        auth: Request-scoped authentication service.
        current_user: Username resolved from the validated session.

    Returns:
        dict: Number of updated accounts.

    Raises:
        HTTPException: If the current password is invalid or the user no longer
            exists.
    """

    changed = await auth.change_password(
        username=current_user, current_password=payload.current_password, new_password=payload.new_password
    )
    if not changed:
        raise HTTPException(status_code=401, detail="invalid_credentials")

    return {"updated": 1}


@router.post("/users", response_model=CreateUserResponse)
async def create_user_endpoint(
    payload: CreateUserRequest,
    auth: AuthService = Depends(get_auth_service),
    _current_admin: str = Depends(require_admin),
) -> dict[str, Any]:
    """Create a new user account (admin only).

    Args:
        payload: User creation payload.

    Returns:
        dict: Created user metadata.
    """

    username = payload.username
    password = payload.password
    role = payload.role
    if await auth.get_user(username):
        raise HTTPException(status_code=409, detail="user_exists")

    return await auth.create_user(username, password, role)


@router.get("/users", response_model=list[UserListItem])
async def list_users_endpoint(
    auth: AuthService = Depends(get_auth_service),
    _current_admin: str = Depends(require_admin),
) -> list[dict[str, Any]]:
    """List all users (admin only).

    Args:
        x_session_token: Session token from request headers.

    Returns:
        list[dict]: User list.
    """
    return await auth.list_users()


@router.post("/users/reset", response_model=ResetPasswordResponse)
async def reset_password_endpoint(
    payload: ResetPasswordRequest,
    auth: AuthService = Depends(get_auth_service),
    _current_admin: str = Depends(require_admin),
) -> dict[str, int]:
    """Reset a user's password (admin only).

    Args:
        payload: Reset payload with username and new password.
        x_session_token: Session token from request headers.

    Returns:
        dict: Update result.
    """

    username = payload.username
    password = payload.password

    updated = await auth.update_password(username, password)
    if updated == 0:
        raise HTTPException(status_code=404, detail="user_not_found")
    return {"updated": updated}


@router.delete("/users/{username}", response_model=DeleteUserResponse)
async def delete_user_endpoint(
    username: str,
    auth: AuthService = Depends(get_auth_service),
    _current_admin: str = Depends(require_account_admin),
) -> dict[str, int]:
    """Delete a user account (admin only).

    Args:
        username: Username to delete.
        x_session_token: Session token from request headers.

    Returns:
        dict: Delete result.
    """

    removed = await auth.delete_user(username, actor=_current_admin)
    if removed == 0:
        raise HTTPException(status_code=404, detail="user_not_found")
    return {"removed": removed}


@router.post("/users/disable", response_model=DisableUserResponse)
async def disable_user_endpoint(
    payload: DisableUserRequest,
    auth: AuthService = Depends(get_auth_service),
    _current_admin: str = Depends(require_account_admin),
) -> dict[str, int | bool]:
    """Disable or enable a user (admin only).

    Args:
        payload: Disable payload with username and disabled flag.
        x_session_token: Session token from request headers.

    Returns:
        dict: Update result.
    """

    username = payload.username
    disabled = bool(payload.disabled)
    updated = await auth.set_user_disabled(username, disabled, actor=_current_admin)
    if updated == 0:
        raise HTTPException(status_code=404, detail="user_not_found")
    return {"updated": updated, "disabled": disabled}


@router.patch("/users/{username}/role", response_model=UpdateRoleResponse)
async def update_role_endpoint(
    username: str,
    payload: UpdateRoleRequest,
    auth: AuthService = Depends(get_auth_service),
    current_admin: str = Depends(require_account_admin),
) -> dict[str, str]:
    """Change another account's role while retaining its active sessions."""
    return await auth.change_role(username, payload.role, actor=current_admin)
