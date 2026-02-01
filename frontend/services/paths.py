import streamlit as st

from services.api import get, post


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


@st.cache_data
def load_path(path_id: int):
    try:
        response = get(f"/paths/{path_id}")
        response.raise_for_status()
        return response.json(), None
    except Exception:
        return None, "Could not load path."
