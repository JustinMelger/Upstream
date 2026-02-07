from datetime import datetime, timezone

import pytest

from backend.core.errors import PathsServiceError
from backend.database import db as db_module
from backend.database.paths_repository import SQLitePathsRepository
from backend.services.paths_service import PathsService


def _clear_paths():
    db_module.init_db()
    with db_module.get_conn() as conn:
        conn.execute("DELETE FROM path_courses")
        conn.execute("DELETE FROM paths")
        conn.execute("DELETE FROM courses")
        conn.commit()


def _create_course(title):
    db_module.init_db()
    with db_module.get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO courses (title, created_at)
            VALUES (?, ?)
            """,
            (title, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()
        return cur.lastrowid


def _paths_service() -> PathsService:
    return PathsService(SQLitePathsRepository(db_module.database))


@pytest.mark.unit
def test_create_path_and_get_courses(app_client):
    """Paths include ordered course lists."""
    _clear_paths()
    paths = _paths_service()
    course_a = _create_course("Course A")
    course_b = _create_course("Course B")

    path = paths.create_path({"name": "Data Path", "description": "Desc", "course_ids": [course_b, course_a]})
    fetched = paths.get_path(path["id"])
    assert fetched["name"] == "Data Path"
    assert [course["id"] for course in fetched["courses"]] == [course_b, course_a]


@pytest.mark.unit
def test_create_path_duplicate_name(app_client):
    """Creating a duplicate path name returns a 409-domain error."""
    _clear_paths()
    paths = _paths_service()
    paths.create_path({"name": "Duplicate", "course_ids": []})
    with pytest.raises(PathsServiceError) as excinfo:
        paths.create_path({"name": "Duplicate", "course_ids": []})
    assert excinfo.value.status_code == 409
    assert str(excinfo.value.detail) == "duplicate_name"


@pytest.mark.unit
def test_update_and_delete_path(app_client):
    """Paths can be updated and deleted."""
    _clear_paths()
    paths = _paths_service()
    course_id = _create_course("Course C")
    path = paths.create_path({"name": "Initial", "description": "", "course_ids": [course_id]})

    updated = paths.update_path(path["id"], {"name": "Updated", "description": "New", "course_ids": []})
    assert updated["name"] == "Updated"
    assert updated["courses"] == []

    assert paths.delete_path(path["id"]) is True
