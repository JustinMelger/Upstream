from __future__ import annotations

from sqlalchemy import Boolean, CheckConstraint, Float, ForeignKey, Index, Integer, Text, text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""


class Course(Base):
    """ORM model for courses."""

    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    provider: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(Text, nullable=True)
    level: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str | None] = mapped_column(Text, nullable=True)


class Tracking(Base):
    """ORM model for course tracking."""

    __tablename__ = "tracking"
    __table_args__ = (UniqueConstraint("colleague_id", "course_id", name="uq_tracking_colleague_course"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    colleague_id: Mapped[str] = mapped_column(Text, nullable=False)
    course_id: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)


class Path(Base):
    """ORM model for learning paths."""

    __tablename__ = "paths"
    __table_args__ = (UniqueConstraint("name", name="uq_paths_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    courses: Mapped[list["PathCourse"]] = relationship(back_populates="path", cascade="all, delete-orphan")


class PathCourse(Base):
    """ORM model mapping paths to ordered courses."""

    __tablename__ = "path_courses"
    __table_args__ = (UniqueConstraint("path_id", "course_id", name="uq_path_courses_path_course"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    path_id: Mapped[int] = mapped_column(ForeignKey("paths.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[int] = mapped_column(Integer, nullable=False)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)

    path: Mapped[Path] = relationship(back_populates="courses")


class Session(Base):
    """ORM model for auth sessions."""

    __tablename__ = "sessions"
    __table_args__ = (
        Index("idx_sessions_token", "token_hash"),
        Index("idx_sessions_colleague", "colleague_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    colleague_id: Mapped[str] = mapped_column(Text, nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    last_seen: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[str] = mapped_column(Text, nullable=False)


class User(Base):
    """ORM model for users."""

    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        Index("idx_users_username", "username"),
        CheckConstraint("role in ('admin', 'user')", name="ck_users_role"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(Text, nullable=False)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)
    last_login_at: Mapped[str | None] = mapped_column(Text, nullable=True)
    disabled: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))


class UserPath(Base):
    """ORM model mapping colleagues to selected paths."""

    __tablename__ = "user_paths"
    __table_args__ = (UniqueConstraint("colleague_id", "path_id", name="uq_user_paths_colleague_path"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    colleague_id: Mapped[str] = mapped_column(Text, nullable=False)
    path_id: Mapped[int] = mapped_column(ForeignKey("paths.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(Text, nullable=True)
