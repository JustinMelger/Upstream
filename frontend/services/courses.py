import pandas as pd
from services.api import delete, get, post
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


def add_course(payload: dict, email: str):
    return post("/courses", json=payload, headers={"X-User-Email": email})


def delete_course(course_id: int, email: str):
    return delete(f"/courses/{course_id}", headers={"X-User-Email": email})
