from fastapi import APIRouter, Header

from backend.core.config import settings


router = APIRouter(prefix="/auth", tags=["auth"])


def _is_admin(email: str | None) -> bool:
    if not email:
        return False
    return email.lower() in settings.admin_emails


@router.get("/role", response_model=dict)
def get_role(x_user_email: str | None = Header(default=None)):
    role = "admin" if _is_admin(x_user_email) else "user"
    return {"role": role}
