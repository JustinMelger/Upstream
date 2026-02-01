import streamlit as st

from services.api import get, post


@st.cache_data
def load_tracking(colleague_id: str):
    if not colleague_id:
        return {}
    try:
        response = get("/tracking", params={"colleague_id": colleague_id})
        response.raise_for_status()
        data = response.json()
    except Exception:
        return {}

    status_map = {}
    for item in data:
        try:
            course_id = int(item.get("course_id", 0))
        except ValueError:
            continue
        status_map[course_id] = item.get("status", "")
    return status_map


@st.cache_data
def load_stats(email: str, colleague_id: str, is_admin: bool):
    params = {}
    if colleague_id and not is_admin:
        params["colleague_id"] = colleague_id
    try:
        response = get(
            "/tracking/stats",
            params=params,
            headers={"X-User-Email": email} if email else {},
        )
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}


def save_status(colleague_id: str, course_id: int, status: str):
    return post(
        "/tracking",
        json={"colleague_id": colleague_id, "course_id": course_id, "status": status},
        headers={"X-User-Email": colleague_id},
    )
