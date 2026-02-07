import pytest

from backend.core.errors import CoursesServiceError
from backend.database import db as db_module
from backend.database.courses_repository import SQLiteCoursesRepository
from backend.services.courses_service import CoursesService


def _clear_courses():
    db_module.init_db()
    with db_module.get_conn() as conn:
        conn.execute("DELETE FROM courses")
        conn.commit()


def _courses_service() -> CoursesService:
    return CoursesService(SQLiteCoursesRepository(db_module.database))


@pytest.mark.unit
def test_create_course_requires_title(app_client):
    """Creating a course without a title returns a 400-domain error."""
    _clear_courses()
    courses = _courses_service()
    with pytest.raises(CoursesServiceError) as excinfo:
        courses.create_course({"title": ""})
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "missing_title"


@pytest.mark.unit
def test_course_list_filters(app_client):
    """Course listing supports query and field filters."""
    _clear_courses()
    courses = _courses_service()
    courses.create_course({"title": "Python Basics", "provider": "ACME", "category": "Dev", "level": "Beginner"})
    courses.create_course({"title": "Advanced SQL", "provider": "DataCorp", "category": "Data", "level": "Advanced"})

    assert len(courses.list_courses(query="python")) == 1
    assert len(courses.list_courses(provider="ACME")) == 1
    assert len(courses.list_courses(category="Data")) == 1
    assert len(courses.list_courses(level="Advanced")) == 1


@pytest.mark.unit
def test_update_and_delete_course(app_client):
    """Courses can be updated and deleted."""
    _clear_courses()
    courses = _courses_service()
    course = courses.create_course({"title": "Cloud 101", "duration_hours": 3})
    course_id = course["id"]

    updated = courses.update_course(course_id, {"title": "Cloud 201", "duration_hours": "bad"})
    assert updated["title"] == "Cloud 201"
    assert updated["duration_hours"] == 3

    assert courses.get_course_by_id(course_id) is not None
    assert courses.delete_course(course_id) is True
    assert courses.get_course_by_id(course_id) is None
