from fastapi import APIRouter, Header, HTTPException

from backend.core.config import settings
from backend.services.auth_service import (
    authenticate_user,
    create_session,
    create_user,
    delete_user,
    get_session,
    get_user,
    has_users,
    is_admin,
    list_users,
    purge_expired_sessions,
    revoke_sessions,
    set_user_disabled,
    update_password,
)


router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=dict)
def login(payload: dict):
    """Authenticate a user and create a session.

    Args:
        payload: Login payload with username and password.

    Returns:
        dict: Session token, expiry, and user metadata.

    Raises:
        HTTPException: If credentials are missing or invalid.
    """
    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    if not username or not password:
        raise HTTPException(status_code=400, detail="missing_fields")

    purge_expired_sessions()

    if not has_users():
        if username != settings.bootstrap_admin_username or password != settings.bootstrap_admin_password:
            raise HTTPException(status_code=401, detail="invalid_credentials")
        user = create_user(username, password, "admin")
        session = create_session(username)
        return {
            "token": session["token"],
            "expires_at": session["expires_at"],
            "username": user["username"],
            "role": user["role"],
            "bootstrap": True,
        }

    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(status_code=401, detail="invalid_credentials")

    session = create_session(username)
    return {"token": session["token"], "expires_at": session["expires_at"], "username": user["username"], "role": user["role"]}


@router.get("/me", response_model=dict)
def me(x_session_token: str | None = Header(default=None)):
    """Return the current authenticated user.

    Args:
        x_session_token: Session token from request headers.

    Returns:
        dict: User metadata and session expiry.
    """
    session = get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    username = session["colleague_id"]
    user = get_user(username)
    if not user:
        raise HTTPException(status_code=401, detail="unauthorized")
    return {"username": user["username"], "role": user["role"], "expires_at": session["expires_at"]}


@router.post("/logout", response_model=dict)
def logout(x_session_token: str | None = Header(default=None)):
    """Revoke all sessions for the current user.

    Args:
        x_session_token: Session token from request headers.

    Returns:
        dict: Number of revoked sessions.
    """
    session = get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    revoked = revoke_sessions(session["colleague_id"])
    return {"revoked": revoked}


@router.get("/role", response_model=dict)
def get_role(x_session_token: str | None = Header(default=None)):
    """Return the role for the current user.

    Args:
        x_session_token: Session token from request headers.

    Returns:
        dict: Role name.
    """
    session = get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    user = get_user(session["colleague_id"])
    if not user:
        raise HTTPException(status_code=401, detail="unauthorized")
    return {"role": user["role"]}


@router.post("/users", response_model=dict)
def create_user_endpoint(payload: dict, x_session_token: str | None = Header(default=None)):
    """Create a new user account (admin only).

    Args:
        payload: User creation payload.
        x_session_token: Session token from request headers.

    Returns:
        dict: Created user metadata.
    """
    session = get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    if not is_admin(session["colleague_id"]):
        raise HTTPException(status_code=403, detail="admin_required")

    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    role = (payload.get("role") or "user").strip()
    if not username or not password:
        raise HTTPException(status_code=400, detail="missing_fields")
    if role not in {"admin", "user"}:
        raise HTTPException(status_code=400, detail="invalid_role")
    if get_user(username):
        raise HTTPException(status_code=409, detail="user_exists")

    return create_user(username, password, role)


@router.get("/users", response_model=list[dict])
def list_users_endpoint(x_session_token: str | None = Header(default=None)):
    """List all users (admin only).

    Args:
        x_session_token: Session token from request headers.

    Returns:
        list[dict]: User list.
    """
    session = get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    if not is_admin(session["colleague_id"]):
        raise HTTPException(status_code=403, detail="admin_required")
    return list_users()


@router.post("/users/reset", response_model=dict)
def reset_password_endpoint(payload: dict, x_session_token: str | None = Header(default=None)):
    """Reset a user's password (admin only).

    Args:
        payload: Reset payload with username and new password.
        x_session_token: Session token from request headers.

    Returns:
        dict: Update result.
    """
    session = get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    if not is_admin(session["colleague_id"]):
        raise HTTPException(status_code=403, detail="admin_required")

    username = (payload.get("username") or "").strip()
    password = (payload.get("password") or "").strip()
    if not username or not password:
        raise HTTPException(status_code=400, detail="missing_fields")

    updated = update_password(username, password)
    if updated == 0:
        raise HTTPException(status_code=404, detail="user_not_found")
    return {"updated": updated}


@router.delete("/users/{username}", response_model=dict)
def delete_user_endpoint(username: str, x_session_token: str | None = Header(default=None)):
    """Delete a user account (admin only).

    Args:
        username: Username to delete.
        x_session_token: Session token from request headers.

    Returns:
        dict: Delete result.
    """
    session = get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    if not is_admin(session["colleague_id"]):
        raise HTTPException(status_code=403, detail="admin_required")

    if session["colleague_id"].lower() == username.lower():
        raise HTTPException(status_code=400, detail="cannot_delete_self")
    removed = delete_user(username)
    return {"removed": removed}


@router.post("/users/disable", response_model=dict)
def disable_user_endpoint(payload: dict, x_session_token: str | None = Header(default=None)):
    """Disable or enable a user (admin only).

    Args:
        payload: Disable payload with username and disabled flag.
        x_session_token: Session token from request headers.

    Returns:
        dict: Update result.
    """
    session = get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    if not is_admin(session["colleague_id"]):
        raise HTTPException(status_code=403, detail="admin_required")

    username = (payload.get("username") or "").strip()
    disabled = bool(payload.get("disabled", True))
    if not username:
        raise HTTPException(status_code=400, detail="missing_fields")
    if session["colleague_id"].lower() == username.lower() and disabled:
        raise HTTPException(status_code=400, detail="cannot_disable_self")

    updated = set_user_disabled(username, disabled)
    if updated == 0:
        raise HTTPException(status_code=404, detail="user_not_found")
    return {"updated": updated, "disabled": disabled}
