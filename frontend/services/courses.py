import pandas as pd
from services.api import delete, get, post, put
import streamlit as st


@st.cache_data
def load_courses():
    try:
        response = get("/courses")
        response.raise_for_status()
        data = response.json()
    except Exception:
        return (
            pd.DataFrame(columns=["title", "provider", "category", "level", "duration_hours", "url"]),
            "Could not reach API.",
        )

    df = pd.DataFrame(data)
    for col in ["title", "provider", "category", "level", "duration_hours", "url", "id"]:
        if col not in df.columns:
            df[col] = ""

    for col in ["title", "provider", "category", "level", "url"]:
        df[col] = df[col].fillna("").astype(str)

    df["duration_hours"] = pd.to_numeric(df["duration_hours"], errors="coerce")
    return df, None


def add_course(payload: dict):
    return post("/courses", json=payload)


def delete_course(course_id: int):
    return delete(f"/courses/{course_id}")


def update_course(course_id: int, payload: dict):
    return put(f"/courses/{course_id}", json=payload)
