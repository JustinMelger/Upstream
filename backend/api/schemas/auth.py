from __future__ import annotations

from backend.api.schemas.common import APIModel


class LoginRequest(APIModel):
    username: str | None = None
    password: str | None = None


class LoginResponse(APIModel):
    token: str
    expires_at: str
    username: str
    role: str
    bootstrap: bool | None = None


class MeResponse(APIModel):
    username: str
    role: str
    expires_at: str


class LogoutResponse(APIModel):
    revoked: int


class RoleResponse(APIModel):
    role: str


class CreateUserRequest(APIModel):
    username: str | None = None
    password: str | None = None
    role: str | None = None


class CreateUserResponse(APIModel):
    username: str
    role: str


class UserListItem(APIModel):
    username: str
    role: str
    created_at: str
    updated_at: str
    last_login_at: str
    disabled: bool


class ResetPasswordRequest(APIModel):
    username: str | None = None
    password: str | None = None


class ResetPasswordResponse(APIModel):
    updated: int


class DeleteUserResponse(APIModel):
    removed: int


class DisableUserRequest(APIModel):
    username: str | None = None
    disabled: bool = True


class DisableUserResponse(APIModel):
    updated: int
    disabled: bool
