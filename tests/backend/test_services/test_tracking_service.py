import pytest

from backend.core.errors import TrackingServiceError
from backend.database.async_repositories.courses import CoursesRepository
from backend.database.async_repositories.tracking import TrackingRepository
from backend.services.courses_service import CoursesService
from backend.services.tracking_service import TrackingService


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_upsert_tracking(db_session):
    """Tracking entries can be added."""
    courses = CoursesService(CoursesRepository(db_session))
    course_id = (await courses.create_course({"title": "T1", "description": "Track me"}))["id"]
    tracking = TrackingService(TrackingRepository(db_session))
    item = await tracking.upsert_tracking("user1", course_id, "interested")
    assert item["status"] == "interested"


@pytest.mark.unit
async def test_upsert_invalid_status(db_session):
    """Invalid tracking status returns a 400-domain error."""
    courses = CoursesService(CoursesRepository(db_session))
    course_id = (await courses.create_course({"title": "T1", "description": "Track me"}))["id"]
    tracking = TrackingService(TrackingRepository(db_session))
    with pytest.raises(TrackingServiceError) as excinfo:
        await tracking.upsert_tracking("user1", course_id, "bad_status")
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_status"


@pytest.mark.unit
async def test_tracking_invalid_payload_type_returns_invalid_payload(db_session):
    """Service-level payload parsing rejects invalid tracking payload types."""
    tracking = TrackingService(TrackingRepository(db_session))
    with pytest.raises(TrackingServiceError) as excinfo:
        await tracking.upsert_tracking("user1", {"bad": 1}, "interested")  # type: ignore[arg-type]
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_payload"


@pytest.mark.unit
async def test_remove_tracking(db_session):
    """Tracking entries can be removed."""
    courses = CoursesService(CoursesRepository(db_session))
    c1 = (await courses.create_course({"title": "C1", "description": "C1"}))["id"]
    tracking = TrackingService(TrackingRepository(db_session))
    await tracking.upsert_tracking("user1", c1, "completed")

    removed = await tracking.remove_tracking("user1", c1)
    assert removed == 1
