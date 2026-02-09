import pytest

from backend.core.errors import TrackingServiceError
from backend.database.async_repositories.tracking import TrackingRepository
from backend.services.tracking_service import TrackingService


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_upsert_and_list_tracking(db_session):
    """Tracking entries can be added and listed."""
    tracking = TrackingService(TrackingRepository(db_session))
    await tracking.upsert_tracking("user1", 1, "interested")
    items = await tracking.list_tracking(colleague_id="user1")
    assert len(items) == 1
    assert items[0]["status"] == "interested"


@pytest.mark.unit
async def test_upsert_invalid_status(db_session):
    """Invalid tracking status returns a 400-domain error."""
    tracking = TrackingService(TrackingRepository(db_session))
    with pytest.raises(TrackingServiceError) as excinfo:
        await tracking.upsert_tracking("user1", 1, "bad_status")
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_status"


@pytest.mark.unit
async def test_stats_and_remove(db_session):
    """Tracking stats aggregate per user and overall."""
    tracking = TrackingService(TrackingRepository(db_session))
    await tracking.upsert_tracking("user1", 1, "completed")
    await tracking.upsert_tracking("user1", 2, "completed")
    await tracking.upsert_tracking("user2", 3, "interested")

    assert (await tracking.stats_for_colleague("user1"))["completed"] == 2
    assert (await tracking.stats_all())["completed"] == 2
    assert (await tracking.stats_by_user())[0]["completed"] >= 0

    removed = await tracking.remove_tracking("user1", 1)
    assert removed == 1
