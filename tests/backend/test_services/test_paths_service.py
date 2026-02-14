import pytest

from backend.core.errors import PathsServiceError
from backend.database.async_repositories.courses import CoursesRepository
from backend.database.async_repositories.paths import PathsRepository
from backend.services.courses_service import CoursesService
from backend.services.paths_service import PathsService


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_create_path_and_get_courses(db_session):
    """Paths include ordered course lists."""
    courses = CoursesService(CoursesRepository(db_session))
    paths = PathsService(PathsRepository(db_session))
    course_a = (await courses.create_course({"title": "Course A", "description": "A"}))["id"]
    course_b = (await courses.create_course({"title": "Course B", "description": "B"}))["id"]

    path = await paths.create_path({"name": "Data Path", "description": "Desc", "course_ids": [course_b, course_a]})
    fetched = await paths.get_path(path["id"])
    assert fetched["name"] == "Data Path"
    assert [course["id"] for course in fetched["courses"]] == [course_b, course_a]


@pytest.mark.unit
async def test_create_path_duplicate_name(db_session):
    """Creating a duplicate path name returns a 409-domain error."""
    paths = PathsService(PathsRepository(db_session))
    await paths.create_path({"name": "Duplicate", "course_ids": []})
    with pytest.raises(PathsServiceError) as excinfo:
        await paths.create_path({"name": "Duplicate", "course_ids": []})
    assert excinfo.value.status_code == 409
    assert str(excinfo.value.detail) == "duplicate_name"


@pytest.mark.unit
async def test_update_and_delete_path(db_session):
    """Paths can be updated and deleted."""
    courses = CoursesService(CoursesRepository(db_session))
    paths = PathsService(PathsRepository(db_session))
    course_id = (await courses.create_course({"title": "Course C", "description": "C"}))["id"]
    path = await paths.create_path({"name": "Initial", "description": "", "course_ids": [course_id]})

    updated = await paths.update_path(path["id"], {"name": "Updated", "description": "New", "course_ids": []})
    assert updated["name"] == "Updated"
    assert updated["courses"] == []

    assert await paths.delete_path(path["id"]) is True
