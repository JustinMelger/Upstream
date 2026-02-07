from fastapi import APIRouter, Depends, Header, HTTPException

from backend.api.deps import get_auth_service
from backend.api.schemas import (
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
from backend.core.config import settings
from backend.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, auth: AuthService = Depends(get_auth_service)):
    """Authenticate a user and create a session.

    Args:
        payload: Login payload with username and password.

    Returns:
        dict: Session token, expiry, and user metadata.

    Raises:
        HTTPException: If credentials are missing or invalid.
    """
    username = (payload.username or "").strip()
    password = (payload.password or "").strip()
    if not username or not password:
        raise HTTPException(status_code=400, detail="missing_fields")

    auth.purge_expired_sessions()

    if not auth.has_users():
        if username != settings.bootstrap_admin_username or password != settings.bootstrap_admin_password:
            raise HTTPException(status_code=401, detail="invalid_credentials")
        user = auth.create_user(username, password, "admin")
        session = auth.create_session(username)
        return {
            "token": session["token"],
            "expires_at": session["expires_at"],
            "username": user["username"],
            "role": user["role"],
            "bootstrap": True,
        }

    user = auth.authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid_credentials")

    session = auth.create_session(username)
    return {
        "token": session["token"],
        "expires_at": session["expires_at"],
        "username": user["username"],
        "role": user["role"],
    }


@router.get("/me", response_model=MeResponse)
def me(
    x_session_token: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),
):
    """Return the current authenticated user.

    Args:
        x_session_token: Session token from request headers.

    Returns:
        dict: User metadata and session expiry.
    """
    session = auth.get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    username = session["colleague_id"]
    user = auth.get_user(username)
    if not user:
        raise HTTPException(status_code=401, detail="unauthorized")
    return {"username": user.username, "role": user.role, "expires_at": session["expires_at"]}


@router.post("/logout", response_model=LogoutResponse)
def logout(
    x_session_token: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),
):
    """Revoke all sessions for the current user.

    Args:
        x_session_token: Session token from request headers.

    Returns:
        dict: Number of revoked sessions.
    """
    session = auth.get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    revoked = auth.revoke_sessions(session["colleague_id"])
    return {"revoked": revoked}


@router.get("/role", response_model=RoleResponse)
def get_role(
    x_session_token: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),
):
    """Return the role for the current user.

    Args:
        x_session_token: Session token from request headers.

    Returns:
        dict: Role name.
    """
    session = auth.get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    user = auth.get_user(session["colleague_id"])
    if not user:
        raise HTTPException(status_code=401, detail="unauthorized")
    return {"role": user.role}


@router.post("/users", response_model=CreateUserResponse)
def create_user_endpoint(
    payload: CreateUserRequest,
    x_session_token: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),
):
    """Create a new user account (admin only).

    Args:
        payload: User creation payload.
        x_session_token: Session token from request headers.

    Returns:
        dict: Created user metadata.
    """
    session = auth.get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    if not auth.is_admin(session["colleague_id"]):
        raise HTTPException(status_code=403, detail="admin_required")

    username = (payload.username or "").strip()
    password = (payload.password or "").strip()
    role = (payload.role or "user").strip()
    if not username or not password:
        raise HTTPException(status_code=400, detail="missing_fields")
    if role not in {"admin", "user"}:
        raise HTTPException(status_code=400, detail="invalid_role")
    if auth.get_user(username):
        raise HTTPException(status_code=409, detail="user_exists")

    return auth.create_user(username, password, role)


@router.get("/users", response_model=list[UserListItem])
def list_users_endpoint(
    x_session_token: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),
):
    """List all users (admin only).

    Args:
        x_session_token: Session token from request headers.

    Returns:
        list[dict]: User list.
    """
    session = auth.get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    if not auth.is_admin(session["colleague_id"]):
        raise HTTPException(status_code=403, detail="admin_required")
    return auth.list_users()


@router.post("/users/reset", response_model=ResetPasswordResponse)
def reset_password_endpoint(
    payload: ResetPasswordRequest,
    x_session_token: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),
):
    """Reset a user's password (admin only).

    Args:
        payload: Reset payload with username and new password.
        x_session_token: Session token from request headers.

    Returns:
        dict: Update result.
    """
    session = auth.get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    if not auth.is_admin(session["colleague_id"]):
        raise HTTPException(status_code=403, detail="admin_required")

    username = (payload.username or "").strip()
    password = (payload.password or "").strip()
    if not username or not password:
        raise HTTPException(status_code=400, detail="missing_fields")

    updated = auth.update_password(username, password)
    if updated == 0:
        raise HTTPException(status_code=404, detail="user_not_found")
    return {"updated": updated}


@router.delete("/users/{username}", response_model=DeleteUserResponse)
def delete_user_endpoint(
    username: str,
    x_session_token: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),
):
    """Delete a user account (admin only).

    Args:
        username: Username to delete.
        x_session_token: Session token from request headers.

    Returns:
        dict: Delete result.
    """
    session = auth.get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    if not auth.is_admin(session["colleague_id"]):
        raise HTTPException(status_code=403, detail="admin_required")

    if session["colleague_id"].lower() == username.lower():
        raise HTTPException(status_code=400, detail="cannot_delete_self")
    removed = auth.delete_user(username)
    return {"removed": removed}


@router.post("/users/disable", response_model=DisableUserResponse)
def disable_user_endpoint(
    payload: DisableUserRequest,
    x_session_token: str | None = Header(default=None),
    auth: AuthService = Depends(get_auth_service),
):
    """Disable or enable a user (admin only).

    Args:
        payload: Disable payload with username and disabled flag.
        x_session_token: Session token from request headers.

    Returns:
        dict: Update result.
    """
    session = auth.get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    if not auth.is_admin(session["colleague_id"]):
        raise HTTPException(status_code=403, detail="admin_required")

    username = (payload.username or "").strip()
    disabled = bool(payload.disabled)
    if not username:
        raise HTTPException(status_code=400, detail="missing_fields")
    if session["colleague_id"].lower() == username.lower() and disabled:
        raise HTTPException(status_code=400, detail="cannot_disable_self")

    updated = auth.set_user_disabled(username, disabled)
    if updated == 0:
        raise HTTPException(status_code=404, detail="user_not_found")
    return {"updated": updated, "disabled": disabled}
