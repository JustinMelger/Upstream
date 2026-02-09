from __future__ import annotations

from pydantic import StrictBool, StrictStr

from backend.api.schemas.common import APIModel


class LoginRequest(APIModel):
    """Login request payload."""

    username: StrictStr | None = None
    password: StrictStr | None = None


class LoginResponse(APIModel):
    """Login response payload."""

    token: str
    expires_at: str
    username: str
    role: str
    bootstrap: bool | None = None


class MeResponse(APIModel):
    """Current-user response payload."""

    username: str
    role: str
    expires_at: str


class LogoutResponse(APIModel):
    """Logout response payload."""

    revoked: int


class RoleResponse(APIModel):
    """Role response payload."""

    role: str


class CreateUserRequest(APIModel):
    """Admin user-create request payload."""

    username: StrictStr | None = None
    password: StrictStr | None = None
    role: StrictStr | None = None


class CreateUserResponse(APIModel):
    """Admin user-create response payload."""

    username: str
    role: str


class UserListItem(APIModel):
    """User list item payload."""

    username: str
    role: str
    created_at: str
    updated_at: str
    last_login_at: str
    disabled: bool


class ResetPasswordRequest(APIModel):
    """Admin reset-password request payload."""

    username: StrictStr | None = None
    password: StrictStr | None = None


class ResetPasswordResponse(APIModel):
    """Admin reset-password response payload."""

    updated: int


class DeleteUserResponse(APIModel):
    """Admin delete-user response payload."""

    removed: int


class DisableUserRequest(APIModel):
    """Admin disable/enable user request payload."""

    username: StrictStr | None = None
    disabled: StrictBool = True


class DisableUserResponse(APIModel):
    """Admin disable/enable user response payload."""

    updated: int
    disabled: bool
