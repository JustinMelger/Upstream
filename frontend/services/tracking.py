from services.api import get, post
import streamlit as st


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
def load_stats(colleague_id: str, is_admin: bool):
    params = {}
    if colleague_id and not is_admin:
        params["colleague_id"] = colleague_id
    try:
        response = get("/tracking/stats", params=params)
        response.raise_for_status()
        return response.json()
    except Exception:
        return {}


def save_status(course_id: int, status: str):
    return post(
        "/tracking",
        json={"course_id": course_id, "status": status},
    )


def delete_status(course_id: int):
    return post("/tracking/delete", json={"course_id": course_id})


@st.cache_data
def load_user_stats():
    try:
        response = get("/tracking/stats/users")
        response.raise_for_status()
        return response.json()
    except Exception:
        return []


@st.cache_data
def load_recent_activity(colleague_id: str, limit: int = 3):
    if not colleague_id:
        return []
    try:
        response = get("/tracking", params={"colleague_id": colleague_id})
        response.raise_for_status()
        data = response.json()
    except Exception:
        return []

    data.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
    return data[:limit]


@st.cache_data
def load_team_recent_activity(limit: int = 5):
    try:
        response = get("/tracking/recent", params={"limit": limit})
        response.raise_for_status()
        return response.json()
    except Exception:
        return []
