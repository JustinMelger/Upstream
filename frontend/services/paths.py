from services.api import delete, get, post, put
import streamlit as st


@st.cache_data
def load_paths():
    try:
        response = get("/paths")
        response.raise_for_status()
        return response.json(), None
    except Exception:
        return [], "Could not reach API."


def add_path(payload: dict):
    return post("/paths", json=payload)


def delete_path(path_id: int):
    return delete(f"/paths/{path_id}")


def update_path(path_id: int, payload: dict):
    return put(f"/paths/{path_id}", json=payload)


@st.cache_data
def load_path(path_id: int):
    try:
        response = get(f"/paths/{path_id}")
        response.raise_for_status()
        return response.json(), None
    except Exception:
        return None, "Could not load path."


def select_path(path_id: int):
    return post(f"/paths/{path_id}/select", json={})


def unselect_path(path_id: int):
    return post(f"/paths/{path_id}/unselect", json={})


@st.cache_data(ttl=5)
def load_selected_paths():
    try:
        response = get("/paths/selected/list")
        response.raise_for_status()
        return response.json()
    except Exception:
        return []
