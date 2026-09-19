from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import secrets

import bcrypt
from pydantic import StrictBool, StrictStr, ValidationError
from pydantic.dataclasses import dataclass
from sqlalchemy.exc import IntegrityError

from backend.core.config import settings
from backend.core.errors import auth_error_handler, AuthServiceError
from backend.database.async_repositories.auth import AuthRepository
from backend.database.models import UserRecord
from backend.database.tx import session_scope


class AuthService:
    """Authentication and session management service."""

    def __init__(self, repo: AuthRepository):
        """Initialize the service.

        Args:
            repo: Persistence repository for auth data.
        """
        self._repo = repo

    def _hash_password(self, password: str) -> str:
        """Hash a password using bcrypt.

        Args:
            password: Plaintext password.

        Returns:
            Hashed password.
        """
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """Verify a password against a bcrypt hash.

        Args:
            password: Plaintext password.
            password_hash: Stored bcrypt hash.

        Returns:
            True if valid.
        """
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except ValueError:
            return False

    def _hash_token(self, token: str) -> str:
        """Hash a session token.

        Args:
            token: Session token.

        Returns:
            SHA256 hash.
        """
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    @staticmethod
    def _parse_username_payload(payload: dict) -> "AuthUsernamePayload":
        """Parse and validate username-only payloads."""
        try:
            return AuthUsernamePayload(**dict(payload or {}))
        except ValidationError as exc:
            raise AuthServiceError(detail="invalid_payload", status_code=400) from exc

    @staticmethod
    def _parse_session_payload(payload: dict) -> "AuthSessionPayload":
        """Parse and validate session payloads."""
        try:
            return AuthSessionPayload(**dict(payload or {}))
        except ValidationError as exc:
            raise AuthServiceError(detail="invalid_payload", status_code=400) from exc

    @staticmethod
    def _parse_create_user_payload(payload: dict) -> "AuthCreateUserPayload":
        """Parse and validate create-user payloads."""
        try:
            return AuthCreateUserPayload(**dict(payload or {}))
        except ValidationError as exc:
            raise AuthServiceError(detail="invalid_payload", status_code=400) from exc

    @staticmethod
    def _parse_update_password_payload(payload: dict) -> "AuthUpdatePasswordPayload":
        """Parse and validate update-password payloads."""
        try:
            return AuthUpdatePasswordPayload(**dict(payload or {}))
        except ValidationError as exc:
            raise AuthServiceError(detail="invalid_payload", status_code=400) from exc

    @staticmethod
    def _parse_set_disabled_payload(payload: dict) -> "AuthSetDisabledPayload":
        """Parse and validate set-user-disabled payloads."""
        try:
            return AuthSetDisabledPayload(**dict(payload or {}))
        except ValidationError as exc:
            raise AuthServiceError(detail="invalid_payload", status_code=400) from exc

    @staticmethod
    def _parse_authenticate_payload(payload: dict) -> "AuthAuthenticatePayload":
        """Parse and validate authenticate-user payloads."""
        try:
            return AuthAuthenticatePayload(**dict(payload or {}))
        except ValidationError as exc:
            raise AuthServiceError(detail="invalid_payload", status_code=400) from exc

    @auth_error_handler()
    async def is_admin(self, username: str | None) -> bool:
        """Check if a user is an admin.

        Args:
            username: Username to check.

        Returns:
            True if admin.
        """
        data = self._parse_username_payload({"username": username})
        candidate = data.username
        if not candidate:
            return False
        user = await self.get_user(candidate)
        return bool(user and user.role == "admin")

    @auth_error_handler()
    async def create_session(self, colleague_id: str) -> dict:
        """Create a new session for a user.

        Args:
            colleague_id: Username to create session for.

        Returns:
            Token and expiry payload.
        """
        data = self._parse_session_payload({"colleague_id": colleague_id})
        candidate = str(data.colleague_id or "").strip()
        user = await self.get_user(candidate)
        if not user:
            raise AuthServiceError(detail="user_not_found", status_code=404)
        username = str(user.username or "").strip()

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.session_days)

        # Token collisions are extremely unlikely, but the database enforces uniqueness on token_hash.
        for _ in range(3):
            token = secrets.token_urlsafe(32)
            token_hash = self._hash_token(token)
            try:
                async with session_scope(self._repo.session):
                    await self._repo.create_session(
                        colleague_id=username,
                        token_hash=token_hash,
                        created_at=now.isoformat(),
                        last_seen=now.isoformat(),
                        expires_at=expires_at.isoformat(),
                    )
                return {"token": token, "expires_at": expires_at.isoformat()}
            except IntegrityError:
                continue

        raise AuthServiceError(detail="session_token_collision", status_code=500)

    @auth_error_handler()
    async def get_session(self, token: str | None) -> dict | None:
        """Validate and load a session by token.

        Args:
            token: Session token.

        Returns:
            Session data or None if invalid/expired.
        """
        data = self._parse_session_payload({"token": token})
        if not data.token:
            return None
        token_hash = self._hash_token(data.token)
        now = datetime.now(timezone.utc)
        async with session_scope(self._repo.session):
            row = await self._repo.get_session(token_hash)
            if not row:
                return None
            user = await self._repo.get_user(row.colleague_id)
            if not user or user.disabled:
                await self._repo.delete_session(token_hash)
                return None
            try:
                expires_at = datetime.fromisoformat(row.expires_at)
            except ValueError:
                return None
            if expires_at < now:
                await self._repo.delete_session(token_hash)
                return None
            await self._repo.update_session_last_seen(token_hash, now.isoformat())
            return {"colleague_id": row.colleague_id, "expires_at": row.expires_at}

    @auth_error_handler()
    async def revoke_session(self, token: str | None) -> int:
        """Revoke only the presented session."""
        if not token:
            return 0
        async with session_scope(self._repo.session):
            return await self._repo.delete_session(self._hash_token(token))

    @auth_error_handler()
    async def revoke_sessions(self, colleague_id: str) -> int:
        """Revoke all sessions for a user.

        Args:
            colleague_id: Username to revoke.

        Returns:
            Number of sessions revoked.
        """
        data = self._parse_session_payload({"colleague_id": colleague_id})
        candidate = str(data.colleague_id or "").strip()
        user = await self.get_user(candidate)
        username = str((user.username if user is not None else candidate) or "").strip()
        async with session_scope(self._repo.session):
            return await self._repo.revoke_sessions(username)

    @auth_error_handler()
    async def get_user(self, username: str) -> UserRecord | None:
        """Fetch a user by username.

        Args:
            username: Username to fetch.

        Returns:
            User record or None.
        """
        data = self._parse_username_payload({"username": username})
        candidate = str(data.username or "").strip()
        async with session_scope(self._repo.session):
            return await self._repo.get_user(candidate)

    @auth_error_handler()
    async def has_users(self) -> bool:
        """Check whether any users exist.

        Returns:
            True if users exist.
        """
        async with session_scope(self._repo.session):
            return await self._repo.has_users()

    @auth_error_handler()
    async def create_user(self, username: str, password: str, role: str) -> dict:
        """Create a new user account.

        Args:
            username: Username.
            password: Plaintext password.
            role: Role name.

        Returns:
            Created user metadata.
        """
        data = self._parse_create_user_payload({"username": username, "password": password, "role": role})
        username_value = str(data.username or "").strip()
        password_value = str(data.password or "")
        role_value = str(data.role or "").strip()
        now = datetime.now(timezone.utc).isoformat()
        password_hash = self._hash_password(password_value)
        async with session_scope(self._repo.session):
            await self._repo.create_user(username_value, password_hash, role_value, now)
        return {"username": username_value, "role": role_value}

    @auth_error_handler()
    async def list_users(self) -> list[dict]:
        """List all users.

        Returns:
            User list.
        """
        async with session_scope(self._repo.session):
            return await self._repo.list_users()

    @auth_error_handler()
    async def update_password(self, username: str, password: str) -> int:
        """Update a user's password.

        Args:
            username: Username.
            password: New plaintext password.

        Returns:
            Number of rows updated.
        """
        data = self._parse_update_password_payload({"username": username, "password": password})
        username_value = str(data.username or "").strip()
        password_value = str(data.password or "")
        now = datetime.now(timezone.utc).isoformat()
        password_hash = self._hash_password(password_value)
        async with session_scope(self._repo.session):
            updated = await self._repo.update_password(username_value, password_hash, now)
            await self._repo.revoke_sessions(username_value)
            return updated

    @auth_error_handler()
    async def delete_user(self, username: str) -> int:
        """Delete a user by username.

        Args:
            username: Username.

        Returns:
            Number of rows deleted.
        """
        data = self._parse_username_payload({"username": username})
        candidate = str(data.username or "").strip()
        async with session_scope(self._repo.session):
            return await self._repo.delete_user(candidate)

    @auth_error_handler()
    async def authenticate_user(self, username: str, password: str) -> dict | None:
        """Authenticate a user with username and password.

        Args:
            username: Username.
            password: Plaintext password.

        Returns:
            User metadata if valid, else None.
        """
        data = self._parse_authenticate_payload({"username": username, "password": password})
        username_value = str(data.username or "").strip()
        password_value = str(data.password or "")
        user = await self.get_user(username_value)
        if not user or user.disabled or not self._verify_password(password_value, user.password_hash):
            return None
        now = datetime.now(timezone.utc).isoformat()
        async with session_scope(self._repo.session):
            await self._repo.update_last_login(username_value, now)
        return {"username": user.username, "role": user.role}

    @auth_error_handler()
    async def change_password(self, username: str, current_password: str, new_password: str) -> bool:
        """Authenticate a user with username and password.

        Args:
            username: Username.
            password: Plaintext password.

        Returns:
            User metadata if valid, else None.
        """
        data = self._parse_authenticate_payload({"username": username, "password": current_password})
        username_value = str(data.username or "").strip()
        password_value = str(data.password or "")
        user = await self.get_user(username_value)
        if not user or user.disabled or not self._verify_password(password_value, user.password_hash):
            return False
        updated = await self.update_password(username=username, password=new_password)
        if updated:
            return True
        return False

    @auth_error_handler()
    async def set_user_disabled(self, username: str, disabled: bool) -> int:
        """Disable or enable a user.

        Args:
            username: Username.
            disabled: True to disable, False to enable.

        Returns:
            Number of rows updated.
        """
        data = self._parse_set_disabled_payload({"username": username, "disabled": disabled})
        username_value = str(data.username or "").strip()
        disabled_value = data.disabled
        if disabled_value is None:
            raise AuthServiceError(detail="invalid_payload", status_code=400)
        now = datetime.now(timezone.utc).isoformat()
        async with session_scope(self._repo.session):
            return await self._repo.set_user_disabled(username_value, disabled_value, now)

    @auth_error_handler()
    async def purge_expired_sessions(self) -> int:
        """Remove expired sessions.

        Returns:
            Number of sessions removed.
        """
        now = datetime.now(timezone.utc).isoformat()
        async with session_scope(self._repo.session):
            return await self._repo.purge_expired_sessions(now)


@dataclass
class AuthUsernamePayload:
    """Typed service-layer payload for username-only calls."""

    username: StrictStr | None = None


@dataclass
class AuthSessionPayload:
    """Typed service-layer payload for session-related calls."""

    colleague_id: StrictStr | None = None
    token: StrictStr | None = None


@dataclass
class AuthCreateUserPayload:
    """Typed service-layer payload for user creation."""

    username: StrictStr | None = None
    password: StrictStr | None = None
    role: StrictStr | None = None


@dataclass
class AuthUpdatePasswordPayload:
    """Typed service-layer payload for password updates."""

    username: StrictStr | None = None
    password: StrictStr | None = None


@dataclass
class AuthSetDisabledPayload:
    """Typed service-layer payload for enabling/disabling users."""

    username: StrictStr | None = None
    disabled: StrictBool | None = None


@dataclass
class AuthAuthenticatePayload:
    """Typed service-layer payload for authentication."""

    username: StrictStr | None = None
    password: StrictStr | None = None
