import pytest

from backend.core.errors import UserPathsServiceError
from backend.database.async_repositories.paths import PathsRepository
from backend.database.async_repositories.user_paths import UserPathsRepository
from backend.services.paths_service import PathsService
from backend.services.user_paths_service import UserPathsService


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_add_remove_user_paths(db_session):
    """Users can add and remove selected paths."""
    paths = PathsService(PathsRepository(db_session))
    user_paths = UserPathsService(UserPathsRepository(db_session))
    path_id = (await paths.create_path({"name": "Starter", "items": []}))["id"]
    await user_paths.add_user_path("user1", path_id)

    removed = await user_paths.remove_user_path("user1", path_id)
    assert removed == 1


@pytest.mark.unit
async def test_update_user_path_status(db_session):
    """User path status updates validate allowed values."""
    paths = PathsService(PathsRepository(db_session))
    user_paths = UserPathsService(UserPathsRepository(db_session))
    path_id = (await paths.create_path({"name": "Advanced", "items": []}))["id"]
    await user_paths.add_user_path("user1", path_id)

    updated = await user_paths.update_user_path_status("user1", path_id, "completed")
    assert updated == 1

    with pytest.raises(UserPathsServiceError) as excinfo:
        await user_paths.update_user_path_status("user1", path_id, "bad_status")
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_status"


@pytest.mark.unit
async def test_add_user_path_missing_path_raises_not_found(db_session):
    """Selecting a missing path returns domain 404 error."""
    user_paths = UserPathsService(UserPathsRepository(db_session))

    with pytest.raises(UserPathsServiceError) as excinfo:
        await user_paths.add_user_path("user1", 999999)
    assert excinfo.value.status_code == 404
    assert str(excinfo.value.detail) == "not_found"


@pytest.mark.unit
async def test_user_paths_invalid_payload_type_returns_invalid_payload(db_session):
    """Service-level payload parsing rejects invalid selected-path payload types."""
    user_paths = UserPathsService(UserPathsRepository(db_session))
    with pytest.raises(UserPathsServiceError) as excinfo:
        await user_paths.add_user_path("user1", {"bad": 1})  # type: ignore[arg-type]
    assert excinfo.value.status_code == 400
    assert str(excinfo.value.detail) == "invalid_payload"
