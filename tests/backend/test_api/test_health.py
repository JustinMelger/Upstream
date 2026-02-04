
def test_health(app_client):
    response = app_client.get("/health")
    assert response.status_code == 200
    assert response.json().get("status") == "ok"
