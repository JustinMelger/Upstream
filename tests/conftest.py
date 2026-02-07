import importlib
import os
from pathlib import Path
import sys

from fastapi.testclient import TestClient
import pytest


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import backend.api.deps as deps
import backend.core.config as config
import backend.database.auth_repository as auth_repository
import backend.database.courses_repository as courses_repository
import backend.database.db as db
import backend.database.paths_repository as paths_repository
import backend.database.tracking_repository as tracking_repository
import backend.database.user_paths_repository as user_paths_repository
import backend.main as main
import backend.services.auth_service as auth_service_module
import backend.services.courses_service as courses_service_module
import backend.services.paths_service as paths_service_module
import backend.services.tracking_service as tracking_service_module
import backend.services.user_paths_service as user_paths_service_module


@pytest.fixture()
def app_client(tmp_path):
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_PATH"] = str(db_path)
    os.environ["SESSION_DAYS"] = "30"
    os.environ["BOOTSTRAP_ADMIN_USERNAME"] = "admin"
    os.environ["BOOTSTRAP_ADMIN_PASSWORD"] = "admin"

    importlib.reload(config)
    importlib.reload(db)
    importlib.reload(auth_repository)
    importlib.reload(courses_repository)
    importlib.reload(paths_repository)
    importlib.reload(tracking_repository)
    importlib.reload(user_paths_repository)
    importlib.reload(auth_service_module)
    importlib.reload(courses_service_module)
    importlib.reload(paths_service_module)
    importlib.reload(tracking_service_module)
    importlib.reload(user_paths_service_module)
    importlib.reload(main)

    db.init_db()
    app = main.app
    app.dependency_overrides = {}

    def _override_auth_service():
        repo = auth_repository.SQLiteAuthRepository(db.database)
        return auth_service_module.AuthService(repo)

    app.dependency_overrides[deps.get_auth_service] = _override_auth_service

    def _override_courses_service():
        repo = courses_repository.SQLiteCoursesRepository(db.database)
        return courses_service_module.CoursesService(repo)

    app.dependency_overrides[deps.get_courses_service] = _override_courses_service

    def _override_paths_service():
        repo = paths_repository.SQLitePathsRepository(db.database)
        return paths_service_module.PathsService(repo)

    app.dependency_overrides[deps.get_paths_service] = _override_paths_service

    def _override_user_paths_service():
        repo = user_paths_repository.SQLiteUserPathsRepository(db.database)
        return user_paths_service_module.UserPathsService(repo)

    app.dependency_overrides[deps.get_user_paths_service] = _override_user_paths_service

    def _override_tracking_service():
        repo = tracking_repository.SQLiteTrackingRepository(db.database)
        return tracking_service_module.TrackingService(repo)

    app.dependency_overrides[deps.get_tracking_service] = _override_tracking_service
    return TestClient(app)
