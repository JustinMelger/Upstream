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
import backend.database.db as db
import backend.main as main
import backend.services.auth_service as auth_service_module


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
    importlib.reload(auth_service_module)
    importlib.reload(main)

    db.init_db()
    app = main.app
    app.dependency_overrides = {}

    def _override_auth_service():
        repo = auth_repository.SQLiteAuthRepository(db.database)
        return auth_service_module.AuthService(repo)

    app.dependency_overrides[deps.get_auth_service] = _override_auth_service
    return TestClient(app)
