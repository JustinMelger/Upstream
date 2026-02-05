from fastapi import Depends, Header, HTTPException

from backend.services.auth_service import auth_service, AuthService


def get_auth_service() -> AuthService:
    """Provide the AuthService dependency.

    Returns:
        AuthService: Shared auth service instance.
    """
    return auth_service


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
