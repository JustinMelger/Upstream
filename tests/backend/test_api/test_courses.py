
def test_courses_requires_auth(app_client):
    response = app_client.get("/courses")
    assert response.status_code == 401
