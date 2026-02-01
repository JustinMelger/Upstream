import sys
from pathlib import Path

import streamlit as st
import pandas as pd

sys.path.append(str(Path(__file__).parent))

from ui.style import apply_global_style
from services.courses import load_courses
from services.paths import load_paths

st.set_page_config(page_title="Home", page_icon="🏠", layout="wide")
apply_global_style()

st.title("Home")
st.caption("A simple learning hub for colleagues.")

st.markdown(
    """
This app is built to create structure around learning from online resources.
"""
)

col1, col2, col3 = st.columns(3)

courses_df, _ = load_courses()
paths, _ = load_paths()

col1.metric("Courses", len(courses_df))
col2.metric("Paths", len(paths))
col3.metric("Providers", courses_df["provider"].replace("", pd.NA).nunique())

st.subheader("How it works")
st.markdown(
    """
- **Browse** curated courses in one place.
- **Track** your progress with simple status updates.
- **Follow** learning paths designed for specific goals.
"""
)

st.subheader("Jump in")
col_a, col_b, col_c = st.columns(3)
with col_a:
    st.page_link("pages/Overview.py", label="Overview", icon="📊")
with col_b:
    st.page_link("pages/Courses.py", label="Courses", icon="📚")
with col_c:
    st.page_link("pages/Paths.py", label="Paths", icon="🧭")

st.markdown(
    """
**Why this exists:** shared learning accelerates onboarding, skill growth, and alignment.
"""
)
