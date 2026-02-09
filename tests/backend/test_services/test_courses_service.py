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


@pytest.mark.unit
async def test_course_list_filters(db_session):
    """Course listing supports query and field filters."""
    courses = CoursesService(CoursesRepository(db_session))
    await courses.create_course({"title": "Python Basics", "provider": "ACME", "category": "Dev", "level": "Beginner"})
    await courses.create_course({"title": "Advanced SQL", "provider": "DataCorp", "category": "Data", "level": "Advanced"})

    assert len(await courses.list_courses(query="python")) == 1
    assert len(await courses.list_courses(provider="ACME")) == 1
    assert len(await courses.list_courses(category="Data")) == 1
    assert len(await courses.list_courses(level="Advanced")) == 1


@pytest.mark.unit
async def test_update_and_delete_course(db_session):
    """Courses can be updated and deleted."""
    courses = CoursesService(CoursesRepository(db_session))
    course = await courses.create_course({"title": "Cloud 101", "duration_hours": 3})
    course_id = course["id"]

    updated = await courses.update_course(course_id, {"title": "Cloud 201", "duration_hours": "bad"})
    assert updated["title"] == "Cloud 201"
    assert updated["duration_hours"] == 3

    assert await courses.get_course_by_id(course_id) is not None
    assert await courses.delete_course(course_id) is True
    assert await courses.get_course_by_id(course_id) is None
