from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import secrets

import bcrypt

from backend.core.config import settings
from backend.core.errors import auth_error_handler
from backend.database.auth_repository import SQLiteAuthRepository
from backend.database.db import database
from backend.database.interfaces import AuthRepository
from backend.database.models import UserRecord


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

    def is_admin(self, username: str | None) -> bool:
        """Check if a user is an admin.

        Args:
            username: Username to check.

        Returns:
            True if admin.
        """
        if not username:
            return False
        user = self.get_user(username)
        return bool(user and user.role == "admin")

    @auth_error_handler()
    def create_session(self, colleague_id: str) -> dict:
        """Create a new session for a user.

        Args:
            colleague_id: Username to create session for.

        Returns:
            Token and expiry payload.
        """
        token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.session_days)

        self._repo.create_session(
            colleague_id=colleague_id,
            token_hash=token_hash,
            created_at=now.isoformat(),
            last_seen=now.isoformat(),
            expires_at=expires_at.isoformat(),
        )

        return {"token": token, "expires_at": expires_at.isoformat()}

    @auth_error_handler()
    def get_session(self, token: str | None) -> dict | None:
        """Validate and load a session by token.

        Args:
            token: Session token.

        Returns:
            Session data or None if invalid/expired.
        """
        if not token:
            return None
        token_hash = self._hash_token(token)
        now = datetime.now(timezone.utc)
        row = self._repo.get_session(token_hash)
        if not row:
            return None
        try:
            expires_at = datetime.fromisoformat(row.expires_at)
        except ValueError:
            return None
        if expires_at < now:
            self._repo.delete_session(token_hash)
            return None
        self._repo.update_session_last_seen(token_hash, now.isoformat())
        return {"colleague_id": row.colleague_id, "expires_at": row.expires_at}

    @auth_error_handler()
    def revoke_sessions(self, colleague_id: str) -> int:
        """Revoke all sessions for a user.

        Args:
            colleague_id: Username to revoke.

        Returns:
            Number of sessions revoked.
        """
        return self._repo.revoke_sessions(colleague_id)

    @auth_error_handler()
    def get_user(self, username: str) -> UserRecord | None:
        """Fetch a user by username.

        Args:
            username: Username to fetch.

        Returns:
            User record or None.
        """
        return self._repo.get_user(username)

    @auth_error_handler()
    def has_users(self) -> bool:
        """Check whether any users exist.

        Returns:
            True if users exist.
        """
        return self._repo.has_users()

    @auth_error_handler()
    def create_user(self, username: str, password: str, role: str) -> dict:
        """Create a new user account.

        Args:
            username: Username.
            password: Plaintext password.
            role: Role name.

        Returns:
            Created user metadata.
        """
        now = datetime.now(timezone.utc).isoformat()
        password_hash = self._hash_password(password)
        self._repo.create_user(username, password_hash, role, now)
        return {"username": username, "role": role}

    @auth_error_handler()
    def list_users(self) -> list[dict]:
        """List all users.

        Returns:
            User list.
        """
        return self._repo.list_users()

    @auth_error_handler()
    def update_password(self, username: str, password: str) -> int:
        """Update a user's password.

        Args:
            username: Username.
            password: New plaintext password.

        Returns:
            Number of rows updated.
        """
        now = datetime.now(timezone.utc).isoformat()
        password_hash = self._hash_password(password)
        return self._repo.update_password(username, password_hash, now)

    @auth_error_handler()
    def delete_user(self, username: str) -> int:
        """Delete a user by username.

        Args:
            username: Username.

        Returns:
            Number of rows deleted.
        """
        return self._repo.delete_user(username)

    @auth_error_handler()
    def authenticate_user(self, username: str, password: str) -> dict | None:
        """Authenticate a user with username and password.

        Args:
            username: Username.
            password: Plaintext password.

        Returns:
            User metadata if valid, else None.
        """
        user = self.get_user(username)
        if not user:
            return None
        if user.disabled:
            return None
        if not self._verify_password(password, user.password_hash):
            return None
        now = datetime.now(timezone.utc).isoformat()
        self._repo.update_last_login(username, now)
        return {"username": user.username, "role": user.role}

    @auth_error_handler()
    def set_user_disabled(self, username: str, disabled: bool) -> int:
        """Disable or enable a user.

        Args:
            username: Username.
            disabled: True to disable, False to enable.

        Returns:
            Number of rows updated.
        """
        now = datetime.now(timezone.utc).isoformat()
        return self._repo.set_user_disabled(username, disabled, now)

    @auth_error_handler()
    def purge_expired_sessions(self) -> int:
        """Remove expired sessions.

        Returns:
            Number of sessions removed.
        """
        now = datetime.now(timezone.utc).isoformat()
        return self._repo.purge_expired_sessions(now)


auth_service = AuthService(SQLiteAuthRepository(database))
