import pytest

from backend.core.errors import PathsServiceError
from backend.database.async_repositories.articles import ArticlesRepository
from backend.database.async_repositories.auth import AuthRepository
from backend.database.async_repositories.courses import CoursesRepository
from backend.database.async_repositories.paths import PathsRepository
from backend.database.async_repositories.videos import VideosRepository
from backend.services.articles_service import ArticlesService
from backend.services.auth_service import AuthService
from backend.services.courses_service import CoursesService
from backend.services.paths_service import PathsService
from backend.services.videos_service import VideosService


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_create_path_and_get_courses(db_session):
    """Paths include ordered course items."""
    courses = CoursesService(CoursesRepository(db_session))
    paths = PathsService(PathsRepository(db_session))
    course_a = (await courses.create_course({"title": "Course A", "description": "A"}))["id"]
    course_b = (await courses.create_course({"title": "Course B", "description": "B"}))["id"]

    path = await paths.create_path(
        {
            "name": "Data Path",
            "description": "Desc",
            "items": [
                {"type": "course", "id": course_b, "position": 0},
                {"type": "course", "id": course_a, "position": 1},
            ],
        }
    )
    fetched = await paths.get_path(path["id"])
    assert fetched["name"] == "Data Path"
    assert [item["id"] for item in fetched["items"]] == [course_b, course_a]


@pytest.mark.unit
async def test_create_path_with_mixed_learning_items(db_session):
    """Paths can store ordered course, video, and article items together."""
    courses = CoursesService(CoursesRepository(db_session))
    videos = VideosService(VideosRepository(db_session))
    articles = ArticlesService(ArticlesRepository(db_session))
    auth = AuthService(AuthRepository(db_session))
    paths = PathsService(PathsRepository(db_session))
    await auth.create_user("admin", "pass123", "admin")

    course_id = (await courses.create_course({"title": "Course A", "description": "A"}))["id"]
    video_id = (
        await videos.create_video(
            payload={
                "title": "Video A",
                "description": "Watch this",
                "provider": "YouTube",
                "category": "Data",
                "url": "https://www.youtube.com/watch?v=test-a",
            },
            created_by="admin",
        )
    )["id"]
    article_id = (
        await articles.create_article(
            payload={"title": "Article A", "url": "https://example.com/article-a"},
            created_by="admin",
        )
    )["id"]

    path = await paths.create_path(
        {
            "name": "Mixed Path",
            "description": "Desc",
            "items": [
                {"type": "video", "id": video_id, "position": 0},
                {"type": "course", "id": course_id, "position": 1},
                {"type": "article", "id": article_id, "position": 2},
            ],
        }
    )
    fetched = await paths.get_path(path["id"])

    assert [item["type"] for item in fetched["items"]] == ["video", "course", "article"]
    assert [item["id"] for item in fetched["items"]] == [video_id, course_id, article_id]
    assert [item["id"] for item in fetched["items"] if item["type"] == "course"] == [course_id]


@pytest.mark.unit
async def test_create_path_duplicate_name(db_session):
    """Creating a duplicate path name returns a 409-domain error."""
    paths = PathsService(PathsRepository(db_session))
    await paths.create_path({"name": "Duplicate", "items": []})
    with pytest.raises(PathsServiceError) as excinfo:
        await paths.create_path({"name": "Duplicate", "items": []})
    assert excinfo.value.status_code == 409
    assert str(excinfo.value.detail) == "duplicate_name"


@pytest.mark.unit
async def test_update_and_delete_path(db_session):
    """Paths can be updated and deleted."""
    courses = CoursesService(CoursesRepository(db_session))
    paths = PathsService(PathsRepository(db_session))
    course_id = (await courses.create_course({"title": "Course C", "description": "C"}))["id"]
    path = await paths.create_path(
        {"name": "Initial", "description": "", "items": [{"type": "course", "id": course_id, "position": 0}]}
    )

    updated = await paths.update_path(path["id"], {"name": "Updated", "description": "New", "items": []})
    assert updated["name"] == "Updated"
    assert updated["items"] == []

    assert await paths.delete_path(path["id"]) is True


@pytest.mark.unit
async def test_create_path_rejects_missing_item_refs(db_session):
    """Typed path item refs must point at existing learning items."""
    paths = PathsService(PathsRepository(db_session))
    with pytest.raises(PathsServiceError) as excinfo:
        await paths.create_path(
            {
                "name": "Broken Path",
                "items": [{"type": "video", "id": 999}],
            }
        )
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_item_refs"


@pytest.mark.unit
async def test_create_path_rejects_duplicate_learning_item_refs(db_session):
    """Paths must not contain the same typed learning item more than once."""
    courses = CoursesService(CoursesRepository(db_session))
    paths = PathsService(PathsRepository(db_session))
    course_id = (await courses.create_course({"title": "Course D", "description": "D"}))["id"]

    with pytest.raises(PathsServiceError) as excinfo:
        await paths.create_path(
            {
                "name": "Duplicate Refs",
                "items": [
                    {"type": "course", "id": course_id, "position": 0},
                    {"type": "course", "id": course_id, "position": 1},
                ],
            }
        )
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "duplicate_item_refs"


@pytest.mark.unit
async def test_update_path_rejects_duplicate_learning_item_refs(db_session):
    """Path updates must reject duplicate typed learning item refs."""
    courses = CoursesService(CoursesRepository(db_session))
    paths = PathsService(PathsRepository(db_session))
    course_id = (await courses.create_course({"title": "Course E", "description": "E"}))["id"]
    path = await paths.create_path({"name": "Path E", "items": [{"type": "course", "id": course_id, "position": 0}]})

    with pytest.raises(PathsServiceError) as excinfo:
        await paths.update_path(
            path["id"],
            {
                "name": "Path E",
                "items": [
                    {"type": "course", "id": course_id, "position": 0},
                    {"type": "course", "id": course_id, "position": 1},
                ],
            },
        )
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "duplicate_item_refs"


@pytest.mark.unit
async def test_create_path_invalid_payload_type_returns_invalid_payload(db_session):
    """Service-level payload parsing rejects invalid types."""
    paths = PathsService(PathsRepository(db_session))
    with pytest.raises(PathsServiceError) as excinfo:
        await paths.create_path({"name": ["bad"], "items": []})
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_payload"


@pytest.mark.unit
async def test_paths_service_works_inside_existing_transaction_scope(db_session):
    """Service methods can run safely when caller already started a transaction."""
    paths = PathsService(PathsRepository(db_session))
    async with db_session.begin():
        created = await paths.create_path({"name": "Nested Path", "items": []})
        listed = await paths.list_paths()
    assert int(created["id"]) > 0
    assert any(str(row.get("name") or "") == "Nested Path" for row in listed)


@pytest.mark.unit
async def test_list_paths_includes_course_count(db_session):
    """Path listings include the number of course items for browse surfaces."""
    courses = CoursesService(CoursesRepository(db_session))
    articles = ArticlesService(ArticlesRepository(db_session))
    auth = AuthService(AuthRepository(db_session))
    paths = PathsService(PathsRepository(db_session))
    await auth.create_user("admin", "pass123", "admin")
    course_a = (await courses.create_course({"title": "Course 1", "description": "A"}))["id"]
    course_b = (await courses.create_course({"title": "Course 2", "description": "B"}))["id"]
    article_id = (
        await articles.create_article(payload={"title": "Article 1", "url": "https://example.com/a"}, created_by="admin")
    )["id"]

    await paths.create_path(
        {
            "name": "Counted Path",
            "items": [
                {"type": "course", "id": course_a, "position": 0},
                {"type": "article", "id": article_id, "position": 1},
                {"type": "course", "id": course_b, "position": 2},
            ],
        }
    )

    listed = await paths.list_paths()
    counted = next(row for row in listed if str(row.get("name") or "") == "Counted Path")
    assert counted["course_count"] == 2
