from __future__ import annotations

from backend.database.db import SQLiteDatabase
from backend.database.models import SessionRecord, UserRecord


class SQLiteAuthRepository:
    """SQLite implementation of auth persistence."""

    def __init__(self, db: SQLiteDatabase):
        """Initialize the repository.

        Args:
            db: SQLite database client.
        """
        self._db = db

    def get_user(self, username: str) -> UserRecord | None:
        """Fetch a user by username.

        Args:
            username: Username to fetch.

        Returns:
            User record or None if not found.
        """
        with self._db.get_conn() as conn:
            row = conn.execute(
                "SELECT username, password_hash, role, disabled FROM users WHERE lower(username) = lower(?)",
                (username,),
            ).fetchone()
        if not row:
            return None
        return UserRecord(
            username=row["username"],
            password_hash=row["password_hash"],
            role=row["role"],
            disabled=bool(row["disabled"]),
        )

    def has_users(self) -> bool:
        """Check whether any users exist.

        Returns:
            True if at least one user exists.
        """
        with self._db.get_conn() as conn:
            row = conn.execute("SELECT 1 FROM users LIMIT 1").fetchone()
        return row is not None

    def create_user(self, username: str, password_hash: str, role: str, now: str) -> None:
        """Insert a new user record.

        Args:
            username: Username.
            password_hash: Password hash.
            role: Role name.
            now: ISO timestamp for created/updated.
        """
        with self._db.get_conn() as conn:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, role, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username, password_hash, role, now, now),
            )
            conn.commit()

    def list_users(self) -> list[dict]:
        """List all users.

        Returns:
            List of user payloads.
        """
        with self._db.get_conn() as conn:
            rows = conn.execute(
                "SELECT username, role, created_at, updated_at, last_login_at, disabled FROM users ORDER BY lower(username) ASC"
            ).fetchall()
        return [
            {
                "username": row["username"],
                "role": row["role"],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
                "last_login_at": row["last_login_at"] or "",
                "disabled": bool(row["disabled"]),
            }
            for row in rows
        ]

    def update_password(self, username: str, password_hash: str, now: str) -> int:
        """Update a user's password hash.

        Args:
            username: Username.
            password_hash: New password hash.
            now: ISO timestamp for updated.

        Returns:
            Number of rows updated.
        """
        with self._db.get_conn() as conn:
            cur = conn.execute(
                """
                UPDATE users
                SET password_hash = ?, updated_at = ?
                WHERE lower(username) = lower(?)
                """,
                (password_hash, now, username),
            )
            conn.commit()
        return cur.rowcount

    def delete_user(self, username: str) -> int:
        """Delete a user by username.

        Args:
            username: Username.

        Returns:
            Number of rows deleted.
        """
        with self._db.get_conn() as conn:
            cur = conn.execute(
                "DELETE FROM users WHERE lower(username) = lower(?)",
                (username,),
            )
            conn.commit()
        return cur.rowcount

    def set_user_disabled(self, username: str, disabled: bool, now: str) -> int:
        """Disable or enable a user.

        Args:
            username: Username.
            disabled: Whether the user should be disabled.
            now: ISO timestamp for updated.

        Returns:
            Number of rows updated.
        """
        with self._db.get_conn() as conn:
            cur = conn.execute(
                "UPDATE users SET disabled = ?, updated_at = ? WHERE lower(username) = lower(?)",
                (1 if disabled else 0, now, username),
            )
            if disabled:
                conn.execute("DELETE FROM sessions WHERE lower(colleague_id) = lower(?)", (username,))
            conn.commit()
        return cur.rowcount

    def create_session(
        self,
        colleague_id: str,
        token_hash: str,
        created_at: str,
        last_seen: str,
        expires_at: str,
    ) -> None:
        """Insert a new session record.

        Args:
            colleague_id: Username for the session.
            token_hash: Hashed token.
            created_at: ISO timestamp for creation.
            last_seen: ISO timestamp for last seen.
            expires_at: ISO timestamp for expiry.
        """
        with self._db.get_conn() as conn:
            conn.execute(
                """
                INSERT INTO sessions (colleague_id, token_hash, created_at, last_seen, expires_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (colleague_id, token_hash, created_at, last_seen, expires_at),
            )
            conn.commit()

    def get_session(self, token_hash: str) -> SessionRecord | None:
        """Fetch a session by token hash.

        Args:
            token_hash: Hashed token.

        Returns:
            Session record or None.
        """
        with self._db.get_conn() as conn:
            row = conn.execute(
                """
                SELECT colleague_id, expires_at
                FROM sessions
                WHERE token_hash = ?
                """,
                (token_hash,),
            ).fetchone()
        if not row:
            return None
        return SessionRecord(colleague_id=row["colleague_id"], expires_at=row["expires_at"])

    def update_session_last_seen(self, token_hash: str, last_seen: str) -> None:
        """Update last_seen for a session.

        Args:
            token_hash: Hashed token.
            last_seen: ISO timestamp for last seen.
        """
        with self._db.get_conn() as conn:
            conn.execute(
                "UPDATE sessions SET last_seen = ? WHERE token_hash = ?",
                (last_seen, token_hash),
            )
            conn.commit()

    def delete_session(self, token_hash: str) -> int:
        """Delete a session by token hash.

        Args:
            token_hash: Hashed token.

        Returns:
            Number of rows deleted.
        """
        with self._db.get_conn() as conn:
            cur = conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
            conn.commit()
        return cur.rowcount

    def revoke_sessions(self, colleague_id: str) -> int:
        """Revoke all sessions for a user.

        Args:
            colleague_id: Username.

        Returns:
            Number of rows deleted.
        """
        with self._db.get_conn() as conn:
            cur = conn.execute("DELETE FROM sessions WHERE colleague_id = ?", (colleague_id,))
            conn.commit()
        return cur.rowcount

    def purge_expired_sessions(self, now: str) -> int:
        """Delete expired sessions.

        Args:
            now: Current ISO timestamp.

        Returns:
            Number of rows deleted.
        """
        with self._db.get_conn() as conn:
            cur = conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
            conn.commit()
        return cur.rowcount

    def update_last_login(self, username: str, now: str) -> None:
        """Update last_login_at for a user.

        Args:
            username: Username.
            now: ISO timestamp for last login.
        """
        with self._db.get_conn() as conn:
            conn.execute(
                "UPDATE users SET last_login_at = ?, updated_at = ? WHERE lower(username) = lower(?)",
                (now, now, username),
            )
            conn.commit()
