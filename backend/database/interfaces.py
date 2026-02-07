from __future__ import annotations

from typing import Protocol

from backend.database.models import CourseRecord, SessionRecord, UserRecord


class AuthRepository(Protocol):
    def get_user(self, username: str) -> UserRecord | None:
        """Fetch a user by username.

        Args:
            username: Username to fetch.

        Returns:
            User record or None if not found.
        """

    def has_users(self) -> bool:
        """Check whether any users exist.

        Returns:
            True if at least one user exists.
        """

    def create_user(self, username: str, password_hash: str, role: str, now: str) -> None:
        """Insert a new user record.

        Args:
            username: Username.
            password_hash: Password hash.
            role: Role name.
            now: ISO timestamp for created/updated.
        """

    def list_users(self) -> list[dict]:
        """List all users.

        Returns:
            List of user payloads.
        """

    def update_password(self, username: str, password_hash: str, now: str) -> int:
        """Update a user's password hash.

        Args:
            username: Username.
            password_hash: New password hash.
            now: ISO timestamp for updated.

        Returns:
            Number of rows updated.
        """

    def delete_user(self, username: str) -> int:
        """Delete a user by username.

        Args:
            username: Username.

        Returns:
            Number of rows deleted.
        """

    def set_user_disabled(self, username: str, disabled: bool, now: str) -> int:
        """Disable or enable a user.

        Args:
            username: Username.
            disabled: Whether the user should be disabled.
            now: ISO timestamp for updated.

        Returns:
            Number of rows updated.
        """

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

    def get_session(self, token_hash: str) -> SessionRecord | None:
        """Fetch a session by token hash.

        Args:
            token_hash: Hashed token.

        Returns:
            Session record or None.
        """

    def update_session_last_seen(self, token_hash: str, last_seen: str) -> None:
        """Update last_seen for a session.

        Args:
            token_hash: Hashed token.
            last_seen: ISO timestamp for last seen.
        """

    def delete_session(self, token_hash: str) -> int:
        """Delete a session by token hash.

        Args:
            token_hash: Hashed token.

        Returns:
            Number of rows deleted.
        """

    def revoke_sessions(self, colleague_id: str) -> int:
        """Revoke all sessions for a user.

        Args:
            colleague_id: Username.

        Returns:
            Number of rows deleted.
        """

    def purge_expired_sessions(self, now: str) -> int:
        """Delete expired sessions.

        Args:
            now: Current ISO timestamp.

        Returns:
            Number of rows deleted.
        """

    def update_last_login(self, username: str, now: str) -> None:
        """Update last_login_at for a user.

        Args:
            username: Username.
            now: ISO timestamp for last login.
        """


class CoursesRepository(Protocol):
    def list_courses(
        self,
        query: str | None,
        provider: str | None,
        category: str | None,
        level: str | None,
    ) -> list[CourseRecord]:
        """List courses with optional filters.

        Args:
            query: Search query.
            provider: Provider filter.
            category: Category filter.
            level: Level filter.

        Returns:
            List of course records.
        """

    def get_course_by_id(self, course_id: int) -> CourseRecord | None:
        """Fetch a course by ID.

        Args:
            course_id: Course ID.

        Returns:
            Course record or None if missing.
        """

    def create_course(
        self,
        title: str,
        provider: str | None,
        category: str | None,
        level: str | None,
        duration_hours: float | None,
        url: str | None,
        created_at: str,
    ) -> int:
        """Create a course.

        Args:
            title: Course title.
            provider: Provider name.
            category: Category name.
            level: Level value.
            duration_hours: Duration in hours.
            url: Course URL.
            created_at: ISO timestamp.

        Returns:
            Created course ID.
        """

    def update_course(
        self,
        course_id: int,
        title: str,
        provider: str | None,
        category: str | None,
        level: str | None,
        duration_hours: float | None,
        url: str | None,
    ) -> int:
        """Update a course.

        Args:
            course_id: Course ID.
            title: Updated title.
            provider: Updated provider.
            category: Updated category.
            level: Updated level.
            duration_hours: Updated duration.
            url: Updated URL.

        Returns:
            Number of rows updated.
        """

    def delete_course(self, course_id: int) -> int:
        """Delete a course by ID.

        Args:
            course_id: Course ID.

        Returns:
            Number of rows deleted.
        """
