import importlib
import os
from pathlib import Path
import sys

from fastapi.testclient import TestClient
import pytest


@pytest.fixture()
def app_client(tmp_path):
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    db_path = tmp_path / "test.db"
    os.environ["DATABASE_PATH"] = str(db_path)
    os.environ["SESSION_DAYS"] = "30"
    os.environ["BOOTSTRAP_ADMIN_USERNAME"] = "admin"
    os.environ["BOOTSTRAP_ADMIN_PASSWORD"] = "admin"

    import backend.core.config as config
    import backend.database.db as db
    import backend.main as main

    importlib.reload(config)
    importlib.reload(db)
    importlib.reload(main)

    db.init_db()
    return TestClient(main.app)
