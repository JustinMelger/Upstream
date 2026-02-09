from __future__ import annotations

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database.models import SessionRecord, UserRecord
from backend.database.orm_models import Session as SessionModel, User as UserModel


class AuthRepository:
    """Async SQLAlchemy implementation of auth persistence."""

    def __init__(self, session: AsyncSession):
        """Initialize the repository.

        Args:
            session: SQLAlchemy AsyncSession for this request.
        """
        self.session = session

    async def get_user(self, username: str) -> UserRecord | None:
        """Fetch a user by username (case-insensitive).

        Args:
            username: Username to look up.

        Returns:
            User record or None.
        """
        result = await self.session.execute(
            select(UserModel).where(func.lower(UserModel.username) == func.lower(username)).limit(1)
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return UserRecord(username=row.username, password_hash=row.password_hash, role=row.role, disabled=bool(row.disabled))

    async def has_users(self) -> bool:
        """Check whether any users exist.

        Returns:
            True if at least one user exists.
        """
        result = await self.session.execute(select(UserModel.id).limit(1))
        return result.first() is not None

    async def create_user(self, username: str, password_hash: str, role: str, now: str) -> None:
        """Create a user record.

        Args:
            username: Username.
            password_hash: Bcrypt password hash.
            role: Role name.
            now: Timestamp (ISO string).
        """
        self.session.add(
            UserModel(
                username=username,
                password_hash=password_hash,
                role=role,
                created_at=now,
                updated_at=now,
                last_login_at=None,
                disabled=False,
            )
        )

    async def list_users(self) -> list[dict]:
        """List users.

        Returns:
            List of user payload dicts.
        """
        result = await self.session.execute(select(UserModel).order_by(func.lower(UserModel.username).asc()))
        rows = result.scalars().all()
        return [
            {
                "username": row.username,
                "role": row.role,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
                "last_login_at": row.last_login_at or "",
                "disabled": bool(row.disabled),
            }
            for row in rows
        ]

    async def update_password(self, username: str, password_hash: str, now: str) -> int:
        """Update a user's password hash.

        Args:
            username: Username to update.
            password_hash: New bcrypt hash.
            now: Timestamp (ISO string).

        Returns:
            Number of rows updated.
        """
        result = await self.session.execute(
            update(UserModel)
            .where(func.lower(UserModel.username) == func.lower(username))
            .values(password_hash=password_hash, updated_at=now)
        )
        return int(result.rowcount or 0)

    async def delete_user(self, username: str) -> int:
        """Delete a user by username.

        Args:
            username: Username to delete.

        Returns:
            Number of rows deleted.
        """
        result = await self.session.execute(delete(UserModel).where(func.lower(UserModel.username) == func.lower(username)))
        return int(result.rowcount or 0)

    async def set_user_disabled(self, username: str, disabled: bool, now: str) -> int:
        """Disable or enable a user.

        Disabling a user also revokes their sessions.

        Args:
            username: Username.
            disabled: True to disable, False to enable.
            now: Timestamp (ISO string).

        Returns:
            Number of rows updated.
        """
        result = await self.session.execute(
            update(UserModel)
            .where(func.lower(UserModel.username) == func.lower(username))
            .values(disabled=disabled, updated_at=now)
        )
        if disabled:
            await self.session.execute(
                delete(SessionModel).where(func.lower(SessionModel.colleague_id) == func.lower(username))
            )
        return int(result.rowcount or 0)

    async def create_session(
        self,
        colleague_id: str,
        token_hash: str,
        created_at: str,
        last_seen: str,
        expires_at: str,
    ) -> None:
        """Insert a session record.

        Args:
            colleague_id: Username for the session.
            token_hash: SHA256 hash of the token.
            created_at: Timestamp (ISO string).
            last_seen: Timestamp (ISO string).
            expires_at: Timestamp (ISO string).
        """
        self.session.add(
            SessionModel(
                colleague_id=colleague_id,
                token_hash=token_hash,
                created_at=created_at,
                last_seen=last_seen,
                expires_at=expires_at,
            )
        )

    async def get_session(self, token_hash: str) -> SessionRecord | None:
        """Fetch a session by token hash.

        Args:
            token_hash: SHA256 hash of the token.

        Returns:
            Session record or None.
        """
        result = await self.session.execute(
            select(SessionModel.colleague_id, SessionModel.expires_at).where(SessionModel.token_hash == token_hash).limit(1)
        )
        row = result.first()
        if not row:
            return None
        colleague_id, expires_at = row
        return SessionRecord(colleague_id=colleague_id, expires_at=expires_at)

    async def update_session_last_seen(self, token_hash: str, last_seen: str) -> None:
        """Update a session's last_seen timestamp.

        Args:
            token_hash: SHA256 hash of the token.
            last_seen: Timestamp (ISO string).
        """
        await self.session.execute(
            update(SessionModel).where(SessionModel.token_hash == token_hash).values(last_seen=last_seen)
        )

    async def delete_session(self, token_hash: str) -> int:
        """Delete a session by token hash.

        Args:
            token_hash: SHA256 hash of the token.

        Returns:
            Number of rows deleted.
        """
        result = await self.session.execute(delete(SessionModel).where(SessionModel.token_hash == token_hash))
        return int(result.rowcount or 0)

    async def revoke_sessions(self, colleague_id: str) -> int:
        """Revoke all sessions for a colleague.

        Args:
            colleague_id: Username.

        Returns:
            Number of sessions revoked.
        """
        result = await self.session.execute(delete(SessionModel).where(SessionModel.colleague_id == colleague_id))
        return int(result.rowcount or 0)

    async def purge_expired_sessions(self, now: str) -> int:
        """Delete expired sessions.

        Args:
            now: Current timestamp (ISO string).

        Returns:
            Number of sessions removed.
        """
        result = await self.session.execute(delete(SessionModel).where(SessionModel.expires_at < now))
        return int(result.rowcount or 0)

    async def update_last_login(self, username: str, now: str) -> None:
        """Update a user's last_login_at timestamp.

        Args:
            username: Username.
            now: Timestamp (ISO string).
        """
        await self.session.execute(
            update(UserModel)
            .where(func.lower(UserModel.username) == func.lower(username))
            .values(last_login_at=now, updated_at=now)
        )
