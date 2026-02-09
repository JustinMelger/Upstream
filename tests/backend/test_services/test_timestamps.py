from datetime import datetime, timezone

import pytest

from backend.database.async_repositories.auth import AuthRepository
from backend.database.async_repositories.courses import CoursesRepository
from backend.database.async_repositories.tracking import TrackingRepository
from backend.services.auth_service import AuthService
from backend.services.courses_service import CoursesService
from backend.services.tracking_service import TrackingService


pytestmark = pytest.mark.anyio


def _assert_iso_utc(value: str) -> None:
    parsed = datetime.fromisoformat(value)
    assert parsed.tzinfo is not None
    assert parsed.utcoffset() == timezone.utc.utcoffset(parsed)


@pytest.mark.unit
async def test_session_and_tracking_timestamps_are_utc_iso8601(db_session):
    """Services emit ISO-8601 timestamps with UTC offsets."""
    auth = AuthService(AuthRepository(db_session))
    await auth.create_user("alice", "pass123", "user")
    session = await auth.create_session("alice")
    _assert_iso_utc(session["expires_at"])

    courses = CoursesService(CoursesRepository(db_session))
    course_id = (await courses.create_course({"title": "Timestamps"}))["id"]

    tracking = TrackingService(TrackingRepository(db_session))
    item = await tracking.upsert_tracking("alice", course_id, "interested")
    _assert_iso_utc(item["updated_at"])
