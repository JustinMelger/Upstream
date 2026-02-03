from fastapi import Header, HTTPException

from backend.services.auth_service import get_session


def require_session(x_session_token: str | None = Header(default=None)) -> str:
    session = get_session(x_session_token)
    if not session:
        raise HTTPException(status_code=401, detail="unauthorized")
    return session["colleague_id"]
