import pytest

from backend.database import db as db_module
from backend.database.user_paths_repository import SQLiteUserPathsRepository
from backend.services.user_paths_service import UserPathsService


def _clear_user_paths():
    db_module.init_db()
    with db_module.get_conn() as conn:
        conn.execute("DELETE FROM user_paths")
        conn.execute("DELETE FROM paths")
        conn.commit()


def _create_path(name):
    db_module.init_db()
    with db_module.get_conn() as conn:
        cur = conn.execute("INSERT INTO paths (name) VALUES (?)", (name,))
        conn.commit()
        return cur.lastrowid


def _user_paths_service() -> UserPathsService:
    return UserPathsService(SQLiteUserPathsRepository(db_module.database))


@pytest.mark.unit
def test_add_list_remove_user_paths(app_client):
    """Users can add, list, and remove selected paths."""
    _clear_user_paths()
    user_paths = _user_paths_service()
    path_id = _create_path("Starter")
    user_paths.add_user_path("user1", path_id)

    paths = user_paths.list_user_paths("user1")
    assert len(paths) == 1
    assert paths[0]["name"] == "Starter"

    removed = user_paths.remove_user_path("user1", path_id)
    assert removed == 1


@pytest.mark.unit
def test_update_user_path_status(app_client):
    """User path status updates validate allowed values."""
    _clear_user_paths()
    user_paths = _user_paths_service()
    path_id = _create_path("Advanced")
    user_paths.add_user_path("user1", path_id)

    updated = user_paths.update_user_path_status("user1", path_id, "completed")
    assert updated == 1

    try:
        user_paths.update_user_path_status("user1", path_id, "bad_status")
        assert False, "Expected ValueError for invalid_status"
    except ValueError as exc:
        assert str(exc) == "invalid_status"
