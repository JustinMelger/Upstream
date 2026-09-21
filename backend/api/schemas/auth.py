from __future__ import annotations

from typing import Literal

from pydantic import field_validator, StrictBool, StrictStr

from backend.api.schemas.common import APIModel


class _UsernameRequest(APIModel):
    """Base request payload with a required normalized username."""

    username: StrictStr

    @field_validator("username")
    @classmethod
    def normalize_username(cls, value: str) -> str:
        """Strip surrounding whitespace and reject blank usernames."""
        username = value.strip()
        if not username:
            raise ValueError("username must not be blank")
        return username


def _validate_present_password(value: str) -> str:
    """Require a nonblank password without altering intentional whitespace."""
    if not value.strip():
        raise ValueError("password must not be blank")

    return value


def _validate_new_password(value: str) -> str:
    """Validate the replacement password policy."""
    _validate_present_password(value)
    if len(value) < 12:
        raise ValueError("password must contain at least 12 characters")

    return value


class LoginRequest(_UsernameRequest):
    """Login request payload."""

    password: StrictStr

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Require a nonblank password."""
        return _validate_present_password(value)


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


class UpdateRoleRequest(APIModel):
    """Administrator-selected account role."""

    role: Literal["admin", "user"]


class UpdateRoleResponse(UpdateRoleRequest):
    """Canonical username and persisted role."""

    username: str


class CreateUserRequest(_UsernameRequest):
    """Admin user-create request payload."""

    password: StrictStr
    role: Literal["admin", "user"] = "user"

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Validate the initial password."""
        return _validate_new_password(value)


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


class ResetPasswordRequest(_UsernameRequest):
    """Admin reset-password request payload."""

    password: StrictStr

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """Validate the replacement password."""
        return _validate_new_password(value)


class ChangePasswordRequest(APIModel):
    """Change password request payload."""

    current_password: StrictStr
    new_password: StrictStr

    @field_validator("current_password")
    @classmethod
    def validate_current_password(cls, value: str) -> str:
        """Require a nonblank current password."""
        return _validate_present_password(value)

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, value: str) -> str:
        """Validate the replacement password policy."""
        return _validate_new_password(value)


class ResetPasswordResponse(APIModel):
    """Admin reset-password response payload."""

    updated: int


class DeleteUserResponse(APIModel):
    """Admin delete-user response payload."""

    removed: int


class DisableUserRequest(_UsernameRequest):
    """Admin disable/enable user request payload."""

    disabled: StrictBool = True


class DisableUserResponse(APIModel):
    """Admin disable/enable user response payload."""

    updated: int
    disabled: bool
