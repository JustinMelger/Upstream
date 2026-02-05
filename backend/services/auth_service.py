from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import secrets

import bcrypt

from backend.core.config import settings
from backend.database.db import get_conn


@dataclass(frozen=True)
class SQLiteDatabase:
    """Database access wrapper for auth services."""

    def get_conn(self):
        return get_conn()


class AuthService:
    """Authentication and session management service."""

    def __init__(self, db: SQLiteDatabase):
        self._db = db

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _verify_password(self, password: str, password_hash: str) -> bool:
        try:
            return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
        except ValueError:
            return False

    def _hash_token(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def is_admin(self, username: str | None) -> bool:
        if not username:
            return False
        user = self.get_user(username)
        return bool(user and user.get("role") == "admin")

    def create_session(self, colleague_id: str) -> dict:
        token = secrets.token_urlsafe(32)
        token_hash = self._hash_token(token)
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.session_days)

        with self._db.get_conn() as conn:
            conn.execute(
                """
                INSERT INTO sessions (colleague_id, token_hash, created_at, last_seen, expires_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    colleague_id,
                    token_hash,
                    now.isoformat(),
                    now.isoformat(),
                    expires_at.isoformat(),
                ),
            )
            conn.commit()

        return {"token": token, "expires_at": expires_at.isoformat()}

    def get_session(self, token: str | None) -> dict | None:
        if not token:
            return None
        token_hash = self._hash_token(token)
        now = datetime.now(timezone.utc)
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
            try:
                expires_at = datetime.fromisoformat(row["expires_at"])
            except ValueError:
                return None
            if expires_at < now:
                conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))
                conn.commit()
                return None
            conn.execute(
                "UPDATE sessions SET last_seen = ? WHERE token_hash = ?",
                (now.isoformat(), token_hash),
            )
            conn.commit()

        return {"colleague_id": row["colleague_id"], "expires_at": row["expires_at"]}

    def revoke_sessions(self, colleague_id: str) -> int:
        with self._db.get_conn() as conn:
            cur = conn.execute("DELETE FROM sessions WHERE colleague_id = ?", (colleague_id,))
            conn.commit()
        return cur.rowcount

    def get_user(self, username: str) -> dict | None:
        with self._db.get_conn() as conn:
            row = conn.execute(
                "SELECT username, password_hash, role, disabled FROM users WHERE lower(username) = lower(?)",
                (username,),
            ).fetchone()
        if not row:
            return None
        return {
            "username": row["username"],
            "password_hash": row["password_hash"],
            "role": row["role"],
            "disabled": bool(row["disabled"]),
        }

    def has_users(self) -> bool:
        with self._db.get_conn() as conn:
            row = conn.execute("SELECT 1 FROM users LIMIT 1").fetchone()
        return row is not None

    def create_user(self, username: str, password: str, role: str) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        password_hash = self._hash_password(password)
        with self._db.get_conn() as conn:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, role, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (username, password_hash, role, now, now),
            )
            conn.commit()
        return {"username": username, "role": role}

    def list_users(self) -> list[dict]:
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

    def update_password(self, username: str, password: str) -> int:
        now = datetime.now(timezone.utc).isoformat()
        password_hash = self._hash_password(password)
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
        with self._db.get_conn() as conn:
            cur = conn.execute(
                "DELETE FROM users WHERE lower(username) = lower(?)",
                (username,),
            )
            conn.commit()
        return cur.rowcount

    def authenticate_user(self, username: str, password: str) -> dict | None:
        user = self.get_user(username)
        if not user:
            return None
        if user["disabled"]:
            return None
        if not self._verify_password(password, user["password_hash"]):
            return None
        now = datetime.now(timezone.utc).isoformat()
        with self._db.get_conn() as conn:
            conn.execute(
                "UPDATE users SET last_login_at = ?, updated_at = ? WHERE lower(username) = lower(?)",
                (now, now, username),
            )
            conn.commit()
        return {"username": user["username"], "role": user["role"]}

    def set_user_disabled(self, username: str, disabled: bool) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._db.get_conn() as conn:
            cur = conn.execute(
                "UPDATE users SET disabled = ?, updated_at = ? WHERE lower(username) = lower(?)",
                (1 if disabled else 0, now, username),
            )
            if disabled:
                conn.execute("DELETE FROM sessions WHERE lower(colleague_id) = lower(?)", (username,))
            conn.commit()
        return cur.rowcount

    def purge_expired_sessions(self) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._db.get_conn() as conn:
            cur = conn.execute("DELETE FROM sessions WHERE expires_at < ?", (now,))
            conn.commit()
        return cur.rowcount


auth_service = AuthService(SQLiteDatabase())
