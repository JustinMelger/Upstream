import pytest

from backend.database.db import get_conn, init_db
from backend.services.user_paths_service import add_user_path, list_user_paths, remove_user_path, update_user_path_status


def _clear_user_paths():
    init_db()
    with get_conn() as conn:
        conn.execute("DELETE FROM user_paths")
        conn.execute("DELETE FROM paths")
        conn.commit()


def _create_path(name):
    init_db()
    with get_conn() as conn:
        cur = conn.execute("INSERT INTO paths (name) VALUES (?)", (name,))
        conn.commit()
        return cur.lastrowid


@pytest.mark.unit
def test_add_list_remove_user_paths(app_client):
    """Users can add, list, and remove selected paths."""
    _clear_user_paths()
    path_id = _create_path("Starter")
    add_user_path("user1", path_id)

    paths = list_user_paths("user1")
    assert len(paths) == 1
    assert paths[0]["name"] == "Starter"

    removed = remove_user_path("user1", path_id)
    assert removed == 1


@pytest.mark.unit
def test_update_user_path_status(app_client):
    """User path status updates validate allowed values."""
    _clear_user_paths()
    path_id = _create_path("Advanced")
    add_user_path("user1", path_id)

    updated = update_user_path_status("user1", path_id, "completed")
    assert updated == 1

    try:
        update_user_path_status("user1", path_id, "bad_status")
        assert False, "Expected ValueError for invalid_status"
    except ValueError as exc:
        assert str(exc) == "invalid_status"
