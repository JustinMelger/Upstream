import pandas as pd
import streamlit as st


def hero_header(df: pd.DataFrame) -> None:
    st.title("Learning Hub")
    st.caption("Focused learning paths and curated courses for teammates.")

    col1, col2, col3 = st.columns(3)
    col1.metric("Courses", len(df))
    col2.metric("Categories", df["category"].replace("", pd.NA).nunique())
    col3.metric("Providers", df["provider"].replace("", pd.NA).nunique())


def format_course_row(row: pd.Series) -> dict:
    return {
        "Title": row.get("title", ""),
        "Provider": row.get("provider", ""),
        "Category": row.get("category", ""),
        "Level": row.get("level", ""),
        "Hours": row.get("duration_hours", ""),
        "URL": row.get("url", ""),
    }
