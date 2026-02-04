import importlib
import os
import tempfile

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def app_client():
    tmp = tempfile.NamedTemporaryFile(delete=False)
    os.environ["DATABASE_PATH"] = tmp.name
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
