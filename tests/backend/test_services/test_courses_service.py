
import pytest

from backend.database.db import get_conn, init_db
from backend.services.courses_service import create_course, delete_course, get_course_by_id, list_courses, update_course


def _clear_courses():

    init_db()
    with get_conn() as conn:
        conn.execute("DELETE FROM courses")
        conn.commit()


@pytest.mark.unit
def test_create_course_requires_title(app_client):
    """Creating a course without a title raises a ValueError."""
    _clear_courses()
    try:
        create_course({"title": ""})
        assert False, "Expected ValueError for missing_title"
    except ValueError as exc:
        assert str(exc) == "missing_title"


@pytest.mark.unit
def test_course_list_filters(app_client):
    """Course listing supports query and field filters."""
    _clear_courses()
    create_course({"title": "Python Basics", "provider": "ACME", "category": "Dev", "level": "Beginner"})
    create_course({"title": "Advanced SQL", "provider": "DataCorp", "category": "Data", "level": "Advanced"})

    assert len(list_courses(query="python")) == 1
    assert len(list_courses(provider="ACME")) == 1
    assert len(list_courses(category="Data")) == 1
    assert len(list_courses(level="Advanced")) == 1


@pytest.mark.unit
def test_update_and_delete_course(app_client):
    """Courses can be updated and deleted."""
    _clear_courses()
    course = create_course({"title": "Cloud 101", "duration_hours": 3})
    course_id = course["id"]

    updated = update_course(course_id, {"title": "Cloud 201", "duration_hours": "bad"})
    assert updated["title"] == "Cloud 201"
    assert updated["duration_hours"] == 3

    assert get_course_by_id(course_id) is not None
    assert delete_course(course_id) is True
    assert get_course_by_id(course_id) is None
