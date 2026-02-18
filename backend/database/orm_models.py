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
    description: Mapped[str] = mapped_column(Text, nullable=False, server_default=text("''"))
    learning_outcomes: Mapped[str | None] = mapped_column(Text, nullable=True)
    prerequisites: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(Text, nullable=True)
    provider: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str | None] = mapped_column(Text, nullable=True)
    level: Mapped[str | None] = mapped_column(Text, nullable=True)
    duration_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.username", ondelete="SET NULL"), nullable=True)


class Tracking(Base):
    """ORM model for course tracking."""

    __tablename__ = "tracking"
    __table_args__ = (UniqueConstraint("colleague_id", "course_id", name="uq_tracking_colleague_course"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    colleague_id: Mapped[str] = mapped_column(Text, nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[str] = mapped_column(Text, nullable=False)


class Path(Base):
    """ORM model for learning paths."""

    __tablename__ = "paths"
    __table_args__ = (UniqueConstraint("name", name="uq_paths_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.username", ondelete="SET NULL"), nullable=True)

    courses: Mapped[list["PathCourse"]] = relationship(back_populates="path", cascade="all, delete-orphan")


class PathCourse(Base):
    """ORM model mapping paths to ordered courses."""

    __tablename__ = "path_courses"
    __table_args__ = (UniqueConstraint("path_id", "course_id", name="uq_path_courses_path_course"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    path_id: Mapped[int] = mapped_column(ForeignKey("paths.id", ondelete="CASCADE"), nullable=False)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    position: Mapped[int | None] = mapped_column(Integer, nullable=True)

    path: Mapped[Path] = relationship(back_populates="courses")


class Session(Base):
    """ORM model for auth sessions."""

    __tablename__ = "sessions"
    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_sessions_token_hash"),
        Index("idx_sessions_token", "token_hash"),
        Index("idx_sessions_colleague", "colleague_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    colleague_id: Mapped[str] = mapped_column(ForeignKey("users.username", ondelete="CASCADE"), nullable=False)
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


class Article(Base):
    """ORM model for shared articles/links."""

    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    tags: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.username", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)


class CourseReview(Base):
    """ORM model for course reviews."""

    __tablename__ = "course_reviews"
    __table_args__ = (
        UniqueConstraint("course_id", "created_by", name="uq_course_reviews_course_created_by"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_course_reviews_rating"),
        Index("idx_course_reviews_course_id", "course_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.username", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)


class PathReview(Base):
    """ORM model for path reviews."""

    __tablename__ = "path_reviews"
    __table_args__ = (
        UniqueConstraint("path_id", "created_by", name="uq_path_reviews_path_created_by"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_path_reviews_rating"),
        Index("idx_path_reviews_path_id", "path_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    path_id: Mapped[int] = mapped_column(ForeignKey("paths.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.username", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)


class ArticleReview(Base):
    """ORM model for article reviews."""

    __tablename__ = "article_reviews"
    __table_args__ = (
        UniqueConstraint("article_id", "created_by", name="uq_article_reviews_article_created_by"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_article_reviews_rating"),
        Index("idx_article_reviews_article_id", "article_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.username", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)


class CourseRecommendation(Base):
    """ORM model for course recommendations."""

    __tablename__ = "course_recommendations"
    __table_args__ = (
        UniqueConstraint("course_id", "created_by", name="uq_course_recommendations_course_created_by"),
        Index("idx_course_recommendations_course_id", "course_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id", ondelete="CASCADE"), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.username", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)


class PathRecommendation(Base):
    """ORM model for path recommendations."""

    __tablename__ = "path_recommendations"
    __table_args__ = (
        UniqueConstraint("path_id", "created_by", name="uq_path_recommendations_path_created_by"),
        Index("idx_path_recommendations_path_id", "path_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    path_id: Mapped[int] = mapped_column(ForeignKey("paths.id", ondelete="CASCADE"), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[str] = mapped_column(ForeignKey("users.username", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[str] = mapped_column(Text, nullable=False)
