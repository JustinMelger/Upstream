
def test_paths_requires_auth(app_client):
    response = app_client.get("/paths")
    assert response.status_code == 401
