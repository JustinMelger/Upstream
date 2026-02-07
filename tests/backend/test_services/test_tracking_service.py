import pytest

from backend.core.errors import TrackingServiceError
from backend.database import db as db_module
from backend.database.tracking_repository import SQLiteTrackingRepository
from backend.services.tracking_service import TrackingService


def _clear_tracking():
    db_module.init_db()
    with db_module.get_conn() as conn:
        conn.execute("DELETE FROM tracking")
        conn.commit()


def _tracking_service() -> TrackingService:
    return TrackingService(SQLiteTrackingRepository(db_module.database))


@pytest.mark.unit
def test_upsert_and_list_tracking(app_client):
    """Tracking entries can be added and listed."""
    _clear_tracking()
    tracking = _tracking_service()
    tracking.upsert_tracking("user1", 1, "interested")
    items = tracking.list_tracking(colleague_id="user1")
    assert len(items) == 1
    assert items[0]["status"] == "interested"


@pytest.mark.unit
def test_upsert_invalid_status(app_client):
    """Invalid tracking status returns a 400-domain error."""
    _clear_tracking()
    tracking = _tracking_service()
    with pytest.raises(TrackingServiceError) as excinfo:
        tracking.upsert_tracking("user1", 1, "bad_status")
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_status"


@pytest.mark.unit
def test_stats_and_remove(app_client):
    """Tracking stats aggregate per user and overall."""
    _clear_tracking()
    tracking = _tracking_service()
    tracking.upsert_tracking("user1", 1, "completed")
    tracking.upsert_tracking("user1", 2, "completed")
    tracking.upsert_tracking("user2", 3, "interested")

    assert tracking.stats_for_colleague("user1")["completed"] == 2
    assert tracking.stats_all()["completed"] == 2
    assert tracking.stats_by_user()[0]["completed"] >= 0

    removed = tracking.remove_tracking("user1", 1)
    assert removed == 1
