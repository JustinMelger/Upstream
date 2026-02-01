from datetime import datetime
from pathlib import Path
import sys

import pandas as pd
import streamlit as st


sys.path.append(str(Path(__file__).parent))

from services.courses import load_courses
from services.paths import load_paths
from ui.style import apply_global_style


st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")
apply_global_style()

st.title("Home")
st.caption("A simple learning hub for colleagues.")

st.markdown(
    """
This app is built to create structure around learning from online resources.
"""
)

st.divider()

col1, col2, col3 = st.columns(3)

courses_df, _ = load_courses()
paths, _ = load_paths()

col1.metric("Courses", len(courses_df))
col2.metric("Paths", len(paths))
col3.metric("Providers", courses_df["provider"].replace("", pd.NA).nunique())

st.divider()

st.subheader("Featured paths")
if not paths:
    st.info("No paths yet. Create one on the Paths page.")
else:
    for path in paths[:3]:
        st.markdown(f"**{path.get('name', '(untitled path)')}**")
        if path.get("description"):
            st.write(path["description"])
        st.page_link("pages/Paths.py", label="View paths", icon="🧭")
        st.divider()

st.subheader("Recently added courses")
if courses_df.empty:
    st.info("No courses yet. Add one on the Courses page.")
else:

    def _format_date(ts: str | None) -> str:
        if not ts:
            return ""
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.strftime("%b %d, %Y")
        except ValueError:
            return ts

    recent = courses_df.sort_values("created_at", ascending=False).head(3)
    for _, row in recent.iterrows():
        added = _format_date(row.get("created_at"))
        date_str = f" ({added})" if added else ""
        st.write(f"• {row['title']} — {row['provider']}{date_str}")

st.divider()

st.markdown(
    """
**Why this exists:** shared learning accelerates onboarding, skill growth, and alignment.
"""
)
