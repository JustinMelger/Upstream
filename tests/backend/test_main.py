import pytest

import backend.main as main


@pytest.mark.integration
def test_health_endpoint(app_client):
    """Main app exposes the health endpoint."""
    response = app_client.get("/health")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"


@pytest.mark.unit
def test_startup_calls_init_and_seed(monkeypatch):
    """Startup event initializes the database and seeds courses."""
    called = {"init": False, "seed": False}

    def fake_init_db():
        called["init"] = True

    def fake_seed(path):
        called["seed"] = True
        assert str(path).endswith("courses.csv")

    monkeypatch.setattr(main, "init_db", fake_init_db)
    monkeypatch.setattr(main, "seed_courses_from_csv", fake_seed)

    main.on_startup()

    assert called["init"] is True
    assert called["seed"] is True
