import pytest

from backend.database.async_repositories.notifications import NotificationsRepository
from backend.services.notifications_service import ActivityEvent, NotificationsService, NotificationsServiceError


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_notifications_activity_invalid_payload_type_returns_invalid_payload(db_session):
    """Service-level payload parsing rejects invalid notifications query payload types."""
    notifications = NotificationsService(NotificationsRepository(db_session))
    with pytest.raises(NotificationsServiceError) as excinfo:
        await notifications.list_activity(current_user=["bad"], limit=30, scope="inbox")  # type: ignore[arg-type]
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_payload"


@pytest.mark.unit
async def test_notifications_activity_invalid_scope_returns_invalid_payload(db_session):
    """Service-level payload parsing rejects unsupported scope values."""
    notifications = NotificationsService(NotificationsRepository(db_session))
    with pytest.raises(NotificationsServiceError) as excinfo:
        await notifications.list_activity(current_user="alice", limit=30, scope="invalid")
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_payload"


@pytest.mark.unit
def test_notifications_finalize_events_dedupes_sorts_and_limits() -> None:
    """Finalization keeps newest deduped rows and applies limit."""
    events = [
        ActivityEvent(
            event_id="course_recommended:1",
            event_type="course_recommended",
            created_at="2026-02-20T10:00:00+00:00",
            actor="alice",
            message="old",
            target_type="course",
            target_id=7,
            target_label="A",
        ),
        ActivityEvent(
            event_id="course_recommended:1",
            event_type="course_recommended",
            created_at="2026-02-20T11:00:00+00:00",
            actor="alice",
            message="new",
            target_type="course",
            target_id=7,
            target_label="A",
        ),
        ActivityEvent(
            event_id="path_rated:2",
            event_type="path_rated",
            created_at="2026-02-20T12:00:00+00:00",
            actor="bob",
            message="rated",
            target_type="path",
            target_id=8,
            target_label="P",
        ),
    ]
    out = NotificationsService._finalize_events(events=events, limit=1)
    assert len(out) == 1
    assert out[0]["event_id"] == "path_rated:2"


@pytest.mark.unit
def test_notifications_build_recommendation_events_inbox_filters_to_owners_content() -> None:
    """Inbox scope should only include recommendations on user's shared content."""
    rows = [
        {
            "recommendation_id": 1,
            "course_id": 11,
            "created_by": "bob",
            "created_at": "2026-02-20T10:00:00+00:00",
            "title": "Course A",
            "course_owner": "alice",
        },
        {
            "recommendation_id": 2,
            "course_id": 12,
            "created_by": "alice",
            "created_at": "2026-02-20T11:00:00+00:00",
            "title": "Course B",
            "course_owner": "alice",
        },
    ]
    out = NotificationsService._build_recommendation_events(rows=rows, username="alice", is_team=False, kind="course")
    assert len(out) == 1
    assert out[0].event_type == "your_course_recommended"
    assert out[0].target_id == 11


@pytest.mark.unit
def test_notifications_build_rating_events_team_sets_you_variant() -> None:
    """Team scope marks actor-owned ratings as you_rated_*."""
    rows = [
        {
            "review_id": 9,
            "article_id": 21,
            "created_by": "alice",
            "created_at": "2026-02-20T10:00:00+00:00",
            "title": "Article",
            "article_owner": "bob",
            "rating": 5,
        }
    ]
    out = NotificationsService._build_rating_events(rows=rows, username="alice", is_team=True, kind="article")
    assert len(out) == 1
    assert out[0].event_type == "you_rated_article"


@pytest.mark.unit
def test_notifications_build_rating_events_supports_video_kind() -> None:
    """Video review events should reuse the generic rating-event builder."""
    rows = [
        {
            "review_id": 12,
            "video_id": 31,
            "created_by": "bob",
            "created_at": "2026-03-18T10:00:00+00:00",
            "title": "Async walkthrough",
            "video_owner": "alice",
            "rating": 4,
        }
    ]
    out = NotificationsService._build_rating_events(rows=rows, username="alice", is_team=False, kind="video")
    assert len(out) == 1
    assert out[0].event_type == "your_video_rated"
    assert out[0].target_type == "video"
