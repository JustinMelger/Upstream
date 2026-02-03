from services.api import delete, get, post


def load_role() -> str:
    try:
        response = get("/auth/role")
        response.raise_for_status()
        data = response.json()
        return data.get("role", "user")
    except Exception:
        return "user"


def login(username: str, password: str):
    return post("/auth/login", json={"username": username, "password": password})


def logout():
    return post("/auth/logout")


def get_me(token: str):
    return get("/auth/me", headers={"X-Session-Token": token})


def create_user(username: str, password: str, role: str):
    return post("/auth/users", json={"username": username, "password": password, "role": role})


def list_users():
    try:
        response = get("/auth/users")
        response.raise_for_status()
        return response.json()
    except Exception:
        return []


def reset_password(username: str, password: str):
    return post("/auth/users/reset", json={"username": username, "password": password})


def delete_user(username: str):
    return delete(f"/auth/users/{username}")


def set_user_disabled(username: str, disabled: bool):
    return post("/auth/users/disable", json={"username": username, "disabled": disabled})
