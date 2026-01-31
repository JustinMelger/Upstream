from backend.core.config import settings


def is_admin(email: str | None) -> bool:
    if not email:
        return False
    return email.lower() in settings.admin_emails
