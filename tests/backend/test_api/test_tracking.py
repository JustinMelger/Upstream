
def test_tracking_requires_auth(app_client):
    response = app_client.get("/tracking")
    assert response.status_code == 401
