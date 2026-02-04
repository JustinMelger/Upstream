from datetime import datetime, timedelta, timezone

import pytest

from backend.database.db import get_conn, init_db
from backend.services.auth_service import (
    authenticate_user,
    create_session,
    create_user,
    get_session,
    get_user,
    is_admin,
    revoke_sessions,
    set_user_disabled,
)


def _clear_auth_tables():
    init_db()
    with get_conn() as conn:
        conn.execute("DELETE FROM sessions")
        conn.execute("DELETE FROM users")
        conn.commit()


@pytest.mark.unit
def test_create_and_authenticate_user(app_client):
    """Users can be created and authenticated with valid credentials."""
    _clear_auth_tables()
    user = create_user("alice", "pass123", "user")
    assert user["username"] == "alice"
    assert get_user("alice") is not None

    authed = authenticate_user("alice", "pass123")
    assert authed["username"] == "alice"


@pytest.mark.unit
def test_authentication_rejects_disabled_user(app_client):
    """Disabled users cannot authenticate."""
    _clear_auth_tables()
    create_user("bob", "pass123", "user")
    set_user_disabled("bob", True)
    assert authenticate_user("bob", "pass123") is None


@pytest.mark.unit
def test_is_admin_checks_role(app_client):
    """Admin role is required for admin checks."""
    _clear_auth_tables()
    create_user("admin1", "pass123", "admin")
    create_user("user1", "pass123", "user")
    assert is_admin("admin1") is True
    assert is_admin("user1") is False


@pytest.mark.unit
def test_session_lifecycle(app_client):
    """Sessions can be created, retrieved, and revoked."""
    _clear_auth_tables()
    token = create_session("carol")["token"]
    session = get_session(token)
    assert session["colleague_id"] == "carol"

    revoked = revoke_sessions("carol")
    assert revoked == 1
    assert get_session(token) is None


@pytest.mark.unit
def test_expired_session_is_purged(app_client):
    """Expired sessions are removed and not returned."""
    _clear_auth_tables()
    token = create_session("dave")["token"]

    past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    with get_conn() as conn:
        conn.execute("UPDATE sessions SET expires_at = ? WHERE colleague_id = ?", (past, "dave"))
        conn.commit()

    assert get_session(token) is None
