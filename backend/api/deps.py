from fastapi import Header, HTTPException

from backend.services.auth_service import auth_service


def require_session(x_session_token: str | None = Header(default=None)) -> str:
    """Validate session token and return the authenticated username.

    Args:
        x_session_token: Session token from request headers.

    Returns:
        str: Authenticated username.

    Raises:
        HTTPException: If the session is missing or invalid.
    """
    session = auth_service.get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    return session["colleague_id"]
