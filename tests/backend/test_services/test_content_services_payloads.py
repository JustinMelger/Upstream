import pytest

from backend.database.async_repositories.article_reviews import ArticleReviewsRepository
from backend.database.async_repositories.articles import ArticlesRepository
from backend.database.async_repositories.course_reviews import CourseReviewsRepository
from backend.database.async_repositories.courses import CoursesRepository
from backend.database.async_repositories.path_reviews import PathReviewsRepository
from backend.database.async_repositories.paths import PathsRepository
from backend.services.article_reviews_service import ArticleReviewsService, ArticleReviewsServiceError
from backend.services.articles_service import ArticlesService, ArticlesServiceError
from backend.services.course_reviews_service import CourseReviewsService, CourseReviewsServiceError
from backend.services.courses_service import CoursesService
from backend.services.path_reviews_service import PathReviewsService, PathReviewsServiceError
from backend.services.paths_service import PathsService


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_create_article_invalid_payload_type_returns_invalid_payload(db_session):
    """Service-level payload parsing rejects invalid article payload types."""
    service = ArticlesService(ArticlesRepository(db_session))
    with pytest.raises(ArticlesServiceError) as excinfo:
        await service.create_article(payload={"title": ["bad"], "url": "https://example.com"}, created_by="admin")
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_payload"


@pytest.mark.unit
async def test_create_course_review_invalid_payload_type_returns_invalid_payload(db_session):
    """Service-level payload parsing rejects invalid course review payload types."""
    courses = CoursesService(CoursesRepository(db_session))
    reviews = CourseReviewsService(CourseReviewsRepository(db_session))
    course_id = int((await courses.create_course({"title": "Course", "description": "Desc"}))["id"])
    with pytest.raises(CourseReviewsServiceError) as excinfo:
        await reviews.create_review(course_id=course_id, payload={"rating": {"bad": 1}, "text": ""}, created_by="admin")
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_payload"


@pytest.mark.unit
async def test_create_path_review_invalid_payload_type_returns_invalid_payload(db_session):
    """Service-level payload parsing rejects invalid path review payload types."""
    paths = PathsService(PathsRepository(db_session))
    reviews = PathReviewsService(PathReviewsRepository(db_session))
    path_id = int((await paths.create_path({"name": "Path", "items": []}))["id"])
    with pytest.raises(PathReviewsServiceError) as excinfo:
        await reviews.create_review(path_id=path_id, payload={"rating": {"bad": 1}, "text": ""}, created_by="admin")
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_payload"


@pytest.mark.unit
async def test_create_article_review_invalid_payload_type_returns_invalid_payload(db_session):
    """Service-level payload parsing rejects invalid article review payload types."""
    reviews = ArticleReviewsService(ArticleReviewsRepository(db_session))
    with pytest.raises(ArticleReviewsServiceError) as excinfo:
        await reviews.create_review(article_id=1, payload={"rating": {"bad": 1}, "text": ""}, created_by="admin")
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_payload"
