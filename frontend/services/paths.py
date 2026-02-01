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


def add_path(payload: dict, email: str):
    return post("/paths", json=payload, headers={"X-User-Email": email})


def delete_path(path_id: int, email: str):
    return delete(f"/paths/{path_id}", headers={"X-User-Email": email})


def update_path(path_id: int, payload: dict, email: str):
    return put(f"/paths/{path_id}", json=payload, headers={"X-User-Email": email})


@st.cache_data
def load_path(path_id: int):
    try:
        response = get(f"/paths/{path_id}")
        response.raise_for_status()
        return response.json(), None
    except Exception:
        return None, "Could not load path."


def select_path(path_id: int, colleague_id: str):
    return post(f"/paths/{path_id}/select", json={"colleague_id": colleague_id})


def unselect_path(path_id: int, colleague_id: str):
    return post(f"/paths/{path_id}/unselect", json={"colleague_id": colleague_id})


@st.cache_data(ttl=5)
def load_selected_paths(colleague_id: str):
    if not colleague_id:
        return []
    try:
        response = get("/paths/selected/list", params={"colleague_id": colleague_id})
        response.raise_for_status()
        return response.json()
    except Exception:
        return []
