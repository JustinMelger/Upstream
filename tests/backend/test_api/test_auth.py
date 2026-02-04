
def test_bootstrap_login(app_client):
    response = app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    assert response.status_code == 200
    data = response.json()
    assert data.get("token")
    assert data.get("role") == "admin"


def test_create_user(app_client):
    login = app_client.post("/auth/login", json={"username": "admin", "password": "admin"})
    token = login.json()["token"]
    response = app_client.post(
        "/auth/users",
        json={"username": "user1", "password": "pass123", "role": "user"},
        headers={"X-Session-Token": token},
    )
    assert response.status_code in (200, 409)
