import pytest

from backend.core.errors import TrackingServiceError
from backend.database.async_repositories.courses import CoursesRepository
from backend.database.async_repositories.tracking import TrackingRepository
from backend.services.courses_service import CoursesService
from backend.services.tracking_service import TrackingService


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_upsert_and_list_tracking(db_session):
    """Tracking entries can be added and listed."""
    courses = CoursesService(CoursesRepository(db_session))
    course_id = (await courses.create_course({"title": "T1"}))["id"]
    tracking = TrackingService(TrackingRepository(db_session))
    await tracking.upsert_tracking("user1", course_id, "interested")
    items = await tracking.list_tracking(colleague_id="user1")
    assert len(items) == 1
    assert items[0]["status"] == "interested"


@pytest.mark.unit
async def test_upsert_invalid_status(db_session):
    """Invalid tracking status returns a 400-domain error."""
    courses = CoursesService(CoursesRepository(db_session))
    course_id = (await courses.create_course({"title": "T1"}))["id"]
    tracking = TrackingService(TrackingRepository(db_session))
    with pytest.raises(TrackingServiceError) as excinfo:
        await tracking.upsert_tracking("user1", course_id, "bad_status")
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_status"


@pytest.mark.unit
async def test_stats_and_remove(db_session):
    """Tracking stats aggregate per user and overall."""
    courses = CoursesService(CoursesRepository(db_session))
    c1 = (await courses.create_course({"title": "C1"}))["id"]
    c2 = (await courses.create_course({"title": "C2"}))["id"]
    c3 = (await courses.create_course({"title": "C3"}))["id"]
    tracking = TrackingService(TrackingRepository(db_session))
    await tracking.upsert_tracking("user1", c1, "completed")
    await tracking.upsert_tracking("user1", c2, "completed")
    await tracking.upsert_tracking("user2", c3, "interested")

    assert (await tracking.stats_for_colleague("user1"))["completed"] == 2
    assert (await tracking.stats_all())["completed"] == 2
    assert (await tracking.stats_by_user())[0]["completed"] >= 0

    removed = await tracking.remove_tracking("user1", c1)
    assert removed == 1
