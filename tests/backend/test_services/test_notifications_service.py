import pytest

from backend.database.async_repositories.notifications import NotificationsRepository
from backend.services.notifications_service import NotificationsService, NotificationsServiceError


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_notifications_activity_invalid_payload_type_returns_invalid_payload(db_session):
    """Service-level payload parsing rejects invalid notifications query payload types."""
    notifications = NotificationsService(NotificationsRepository(db_session))
    with pytest.raises(NotificationsServiceError) as excinfo:
        await notifications.list_activity(current_user=["bad"], limit=30, scope="inbox")  # type: ignore[arg-type]
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_payload"
