from __future__ import annotations

from pydantic import StrictBool, StrictStr

from backend.api.schemas.common import APIModel


class LoginRequest(APIModel):
    username: StrictStr | None = None
    password: StrictStr | None = None


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
    username: StrictStr | None = None
    password: StrictStr | None = None
    role: StrictStr | None = None


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
    username: StrictStr | None = None
    password: StrictStr | None = None


class ResetPasswordResponse(APIModel):
    updated: int


class DeleteUserResponse(APIModel):
    removed: int


class DisableUserRequest(APIModel):
    username: StrictStr | None = None
    disabled: StrictBool = True


class DisableUserResponse(APIModel):
    updated: int
    disabled: bool
