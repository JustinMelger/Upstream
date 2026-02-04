
from datetime import datetime, timezone

import pytest

from backend.database.db import get_conn, init_db
from backend.services.paths_service import create_path, delete_path, get_path, update_path


def _clear_paths():

    init_db()
    with get_conn() as conn:
        conn.execute("DELETE FROM path_courses")
        conn.execute("DELETE FROM paths")
        conn.execute("DELETE FROM courses")
        conn.commit()


def _create_course(title):
    init_db()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO courses (title, created_at)
            VALUES (?, ?)
            """,
            (title, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        return cur.lastrowid


@pytest.mark.unit
def test_create_path_and_get_courses(app_client):
    """Paths include ordered course lists."""
    _clear_paths()
    course_a = _create_course("Course A")
    course_b = _create_course("Course B")

    path = create_path({"name": "Data Path", "description": "Desc", "course_ids": [course_b, course_a]})
    fetched = get_path(path["id"])
    assert fetched["name"] == "Data Path"
    assert [course["id"] for course in fetched["courses"]] == [course_b, course_a]


@pytest.mark.unit
def test_create_path_duplicate_name(app_client):
    """Creating a duplicate path name raises ValueError."""
    _clear_paths()
    create_path({"name": "Duplicate", "course_ids": []})
    try:
        create_path({"name": "Duplicate", "course_ids": []})
        assert False, "Expected ValueError for duplicate_name"
    except ValueError as exc:
        assert str(exc) == "duplicate_name"


@pytest.mark.unit
def test_update_and_delete_path(app_client):
    """Paths can be updated and deleted."""
    _clear_paths()
    course_id = _create_course("Course C")
    path = create_path({"name": "Initial", "description": "", "course_ids": [course_id]})

    updated = update_path(path["id"], {"name": "Updated", "description": "New", "course_ids": []})
    assert updated["name"] == "Updated"
    assert updated["courses"] == []

    assert delete_path(path["id"]) is True
