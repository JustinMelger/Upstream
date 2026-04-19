from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from backend.database.async_repositories.auth import AuthRepository
from backend.services.auth_service import AuthService, AuthServiceError


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_create_and_authenticate_user(db_session):
    """Users can be created and authenticated with valid credentials."""
    auth_service = AuthService(AuthRepository(db_session))
    user = await auth_service.create_user("alice", "pass123", "user")
    assert user["username"] == "alice"
    assert await auth_service.get_user("alice") is not None

    authed = await auth_service.authenticate_user("alice", "pass123")
    assert authed["username"] == "alice"


@pytest.mark.unit
async def test_authentication_rejects_disabled_user(db_session):
    """Disabled users cannot authenticate."""
    auth_service = AuthService(AuthRepository(db_session))
    await auth_service.create_user("bob", "pass123", "user")
    await auth_service.set_user_disabled("bob", True)
    assert await auth_service.authenticate_user("bob", "pass123") is None


@pytest.mark.unit
async def test_is_admin_checks_role(db_session):
    """Admin role is required for admin checks."""
    auth_service = AuthService(AuthRepository(db_session))
    await auth_service.create_user("admin1", "pass123", "admin")
    await auth_service.create_user("user1", "pass123", "user")
    assert await auth_service.is_admin("admin1") is True
    assert await auth_service.is_admin("user1") is False


@pytest.mark.unit
async def test_session_lifecycle(db_session):
    """Sessions can be created, retrieved, and revoked."""
    auth_service = AuthService(AuthRepository(db_session))
    await auth_service.create_user("carol", "pass123", "user")
    token = (await auth_service.create_session("carol"))["token"]
    session = await auth_service.get_session(token)
    assert session["colleague_id"] == "carol"

    revoked = await auth_service.revoke_sessions("carol")
    assert revoked == 1
    assert await auth_service.get_session(token) is None


@pytest.mark.unit
async def test_session_creation_and_revocation_use_canonical_username(db_session):
    """Mixed-case auth inputs should resolve to the stored username casing."""
    auth_service = AuthService(AuthRepository(db_session))
    await auth_service.create_user("Alice", "pass123", "user")

    token = (await auth_service.create_session("alice"))["token"]
    session = await auth_service.get_session(token)
    assert session is not None
    assert session["colleague_id"] == "Alice"

    revoked = await auth_service.revoke_sessions("ALICE")
    assert revoked == 1
    assert await auth_service.get_session(token) is None


@pytest.mark.unit
async def test_expired_session_is_purged(db_session):
    """Expired sessions are removed and not returned."""
    auth_service = AuthService(AuthRepository(db_session))
    await auth_service.create_user("dave", "pass123", "user")
    token = (await auth_service.create_session("dave"))["token"]

    past = datetime.now(timezone.utc) - timedelta(days=1)
    async with db_session.begin():
        await db_session.execute(
            text("UPDATE sessions SET expires_at = :past WHERE colleague_id = :cid"), {"past": past, "cid": "dave"}
        )

    assert await auth_service.get_session(token) is None


@pytest.mark.unit
async def test_create_user_invalid_payload_type_returns_invalid_payload(db_session):
    """Service-level payload parsing rejects invalid create-user payload types."""
    auth_service = AuthService(AuthRepository(db_session))
    with pytest.raises(AuthServiceError) as excinfo:
        await auth_service.create_user(["bad"], "pass123", "user")  # type: ignore[arg-type]
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_payload"


@pytest.mark.unit
async def test_set_user_disabled_invalid_payload_type_returns_invalid_payload(db_session):
    """Service-level payload parsing rejects invalid set-disabled payload types."""
    auth_service = AuthService(AuthRepository(db_session))
    with pytest.raises(AuthServiceError) as excinfo:
        await auth_service.set_user_disabled("alice", {"bad": True})  # type: ignore[arg-type]
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_payload"
