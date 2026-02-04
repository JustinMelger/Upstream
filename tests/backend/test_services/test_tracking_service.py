
import pytest

from backend.database.db import get_conn, init_db
from backend.services.tracking_service import (
    list_tracking,
    remove_tracking,
    stats_all,
    stats_by_user,
    stats_for_colleague,
    upsert_tracking,
)


def _clear_tracking():

    init_db()
    with get_conn() as conn:
        conn.execute("DELETE FROM tracking")
        conn.commit()


@pytest.mark.unit
def test_upsert_and_list_tracking(app_client):
    """Tracking entries can be added and listed."""
    _clear_tracking()
    upsert_tracking("user1", 1, "interested")
    items = list_tracking(colleague_id="user1")
    assert len(items) == 1
    assert items[0]["status"] == "interested"


@pytest.mark.unit
def test_upsert_invalid_status(app_client):
    """Invalid tracking status raises ValueError."""
    _clear_tracking()
    try:
        upsert_tracking("user1", 1, "bad_status")
        assert False, "Expected ValueError for invalid_status"
    except ValueError as exc:
        assert str(exc) == "invalid_status"


@pytest.mark.unit
def test_stats_and_remove(app_client):
    """Tracking stats aggregate per user and overall."""
    _clear_tracking()
    upsert_tracking("user1", 1, "completed")
    upsert_tracking("user1", 2, "completed")
    upsert_tracking("user2", 3, "interested")

    assert stats_for_colleague("user1")["completed"] == 2
    assert stats_all()["completed"] == 2
    assert stats_by_user()[0]["completed"] >= 0

    removed = remove_tracking("user1", 1)
    assert removed == 1
