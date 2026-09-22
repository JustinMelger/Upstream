import pytest

from backend.core.errors import CoursesServiceError
from backend.database.async_repositories.courses import CoursesRepository
from backend.services.courses_service import CoursesService


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_create_course_requires_title(db_session):
    """Creating a course without a title returns a 400-domain error."""
    courses = CoursesService(CoursesRepository(db_session))
    with pytest.raises(CoursesServiceError) as excinfo:
        await courses.create_course({"title": ""})
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "missing_title"

    with pytest.raises(CoursesServiceError) as excinfo:
        await courses.create_course({"title": "Missing description"})
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "missing_description"


@pytest.mark.unit
async def test_update_and_delete_course(db_session):
    """Courses can be updated and deleted."""
    courses = CoursesService(CoursesRepository(db_session))
    course = await courses.create_course(
        {
            "title": "Cloud 101",
            "description": "Cloud intro",
            "learning_outcomes": "Understand cloud fundamentals",
            "prerequisites": "General software basics",
            "language": "English",
            "duration_hours": 3,
        }
    )
    course_id = course["id"]
    assert course["language"] == "English"
    assert "Understand cloud fundamentals" in course["search_document"]

    updated = await courses.update_course(
        course_id,
        {
            "title": "Cloud 201",
            "description": "Cloud advanced",
            "learning_outcomes": "Deploy cloud workloads",
            "prerequisites": "Cloud fundamentals",
            "language": "Spanish",
            "duration_hours": "bad",
        },
    )
    assert updated["title"] == "Cloud 201"
    assert updated["duration_hours"] == 3
    assert updated["language"] == "Spanish"
    assert "Deploy cloud workloads" in updated["search_document"]

    assert await courses.get_course_by_id(course_id) is not None
    assert await courses.delete_course(course_id) is True
    assert await courses.get_course_by_id(course_id) is None


@pytest.mark.unit
async def test_create_course_invalid_payload_type_returns_invalid_payload(db_session):
    """Service-level payload parsing rejects invalid types."""
    courses = CoursesService(CoursesRepository(db_session))
    with pytest.raises(CoursesServiceError) as excinfo:
        await courses.create_course({"title": ["bad"], "description": "desc"})
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_payload"


@pytest.mark.unit
async def test_courses_service_works_inside_existing_transaction_scope(db_session):
    """Service methods can run safely when caller already started a transaction."""
    courses = CoursesService(CoursesRepository(db_session))
    async with db_session.begin():
        created = await courses.create_course({"title": "Nested Tx", "description": "Nested tx"})
        detail = await courses.get_course_by_id(int(created["id"]))
    assert int(created["id"]) > 0
    assert detail is not None


@pytest.mark.unit
async def test_courses_reads_keep_empty_images_without_http(db_session, monkeypatch):
    """Creation and detail reads never fetch external resource artwork."""
    import httpx

    async def unexpected_http(*args, **kwargs):
        raise AssertionError("Content reads must not fetch URLs")

    monkeypatch.setattr(httpx.AsyncClient, "send", unexpected_http)
    service = CoursesService(CoursesRepository(db_session))
    created = await service.create_course(
        {"title": "Resource", "description": "Summary", "url": "https://example.com/resource"}
    )

    detail = await service.get_course_by_id(course_id=int(created["id"]))
    assert detail["preview_image_url"] == ""
