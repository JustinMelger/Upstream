from datetime import datetime, timezone

import pytest

from backend.database.async_repositories.article_reviews import ArticleReviewsRepository
from backend.database.async_repositories.articles import ArticlesRepository
from backend.database.async_repositories.auth import AuthRepository
from backend.database.async_repositories.course_reviews import CourseReviewsRepository
from backend.database.async_repositories.courses import CoursesRepository, CreateCoursePayload
from backend.database.async_repositories.path_reviews import PathReviewsRepository
from backend.database.async_repositories.paths import PathsRepository
from backend.database.async_repositories.tracking import TrackingRepository
from backend.database.async_repositories.user_paths import UserPathsRepository
from backend.services.auth_service import AuthService
from backend.services.courses_service import CoursesService
from backend.services.paths_service import PathsService
from backend.services.tracking_service import TrackingService


pytestmark = pytest.mark.anyio


def _assert_iso_utc(value: str) -> None:
    parsed = datetime.fromisoformat(value)
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == timezone.utc.utcoffset(parsed)


@pytest.mark.unit
async def test_session_and_tracking_timestamps_are_utc_iso8601(db_session):
    """Services emit ISO-8601 timestamps with UTC offsets."""
    auth = AuthService(AuthRepository(db_session))
    await auth.create_user("alice", "test-password-123", "user")
    session = await auth.create_session("alice")
    _assert_iso_utc(session["expires_at"])

    courses = CoursesService(CoursesRepository(db_session))
    course_id = (await courses.create_course({"title": "Timestamps", "description": "Timestamps course"}))["id"]

    tracking = TrackingService(TrackingRepository(db_session))
    item = await tracking.upsert_tracking("alice", course_id, "interested")
    _assert_iso_utc(item["updated_at"])


@pytest.mark.unit
async def test_auth_repo_list_users_returns_iso_strings_with_datetime_input(db_session):
    """AuthRepository accepts datetime timestamps and still emits ISO strings."""
    repo = AuthRepository(db_session)
    now = datetime.now(timezone.utc)
    async with db_session.begin():
        await repo.create_user("eve", "hash", "user", now)
        await repo.update_last_login("eve", now)
    users = await repo.list_users()
    row = next(u for u in users if str(u.get("username")) == "eve")
    _assert_iso_utc(str(row.get("created_at") or ""))
    _assert_iso_utc(str(row.get("updated_at") or ""))
    _assert_iso_utc(str(row.get("last_login_at") or ""))


@pytest.mark.unit
async def test_user_paths_repo_accepts_datetime_timestamps(db_session):
    """UserPathsRepository accepts datetime timestamps for add/update flows."""
    paths = PathsService(PathsRepository(db_session))
    repo = UserPathsRepository(db_session)
    path_id = (await paths.create_path({"name": "Timestamp Path", "items": []}))["id"]
    now = datetime.now(timezone.utc)
    async with db_session.begin():
        inserted = await repo.add_user_path("alice", int(path_id), now)
        updated = await repo.update_user_path_status("alice", int(path_id), "completed", now)
    assert inserted == 1
    assert updated == 1


@pytest.mark.unit
async def test_content_and_review_repos_accept_datetime_and_return_iso(db_session):
    """Timestamp-migrated content and review repos keep ISO string contract."""
    auth = AuthService(AuthRepository(db_session))
    await auth.create_user("alice", "test-password-123", "user")

    courses_repo = CoursesRepository(db_session)
    paths = PathsService(PathsRepository(db_session))
    articles_repo = ArticlesRepository(db_session)
    course_reviews = CourseReviewsRepository(db_session)
    path_reviews = PathReviewsRepository(db_session)
    article_reviews = ArticleReviewsRepository(db_session)
    now = datetime.now(timezone.utc)
    async with db_session.begin():
        course_id = await courses_repo.create_course(
            payload=CreateCoursePayload(
                title="Temporal course",
                description="d",
                learning_outcomes=None,
                prerequisites=None,
                language=None,
                provider=None,
                category=None,
                level=None,
                duration_hours=None,
                url=None,
                created_at=now,
                created_by="alice",
            )
        )
        article_id = await articles_repo.create_article(
            title="Temporal article",
            url="https://example.com",
            tags=None,
            created_by="alice",
            created_at=now,
        )

    path_id = (
        await paths.create_path({"name": "Temporal path", "items": [{"type": "course", "id": int(course_id), "position": 0}]})
    )["id"]

    async with db_session.begin():
        await course_reviews.create_review(
            course_id=int(course_id),
            rating=5,
            text="great",
            created_by="alice",
            created_at=now,
        )
        await path_reviews.create_review(
            path_id=int(path_id),
            rating=4,
            text="nice",
            created_by="alice",
            created_at=now,
        )
        await article_reviews.create_review(
            article_id=int(article_id),
            rating=4,
            text="solid",
            created_by="alice",
            created_at=now,
        )
    course = await courses_repo.get_course_by_id(int(course_id))
    article = await articles_repo.get_article_by_id(int(article_id))
    c_review = (await course_reviews.list_for_course(course_id=int(course_id)))[0]
    p_review = (await path_reviews.list_for_path(path_id=int(path_id)))[0]
    a_review = (await article_reviews.list_for_article(article_id=int(article_id)))[0]

    assert course is not None and article is not None
    _assert_iso_utc(str(course.created_at or ""))
    _assert_iso_utc(str(article.created_at or ""))
    _assert_iso_utc(str(c_review.created_at or ""))
    _assert_iso_utc(str(p_review.created_at or ""))
    _assert_iso_utc(str(a_review.created_at or ""))
