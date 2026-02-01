import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).parent))

from ui.style import apply_global_style
from ui.components import hero_header
from services.courses import load_courses
from services.tracking import load_stats

st.set_page_config(page_title="Learning Hub", page_icon="📚", layout="wide")
apply_global_style()

st.title("Learning Hub")
st.caption("Overview of courses and progress.")

courses_df, load_error = load_courses()
if load_error:
    st.error(load_error)

hero_header(courses_df)

st.subheader("📈 Progress snapshot")
email = st.text_input("Your name or email", "")
col1, col2, col3 = st.columns(3)

stats = load_stats(email.strip(), email.strip(), False)

col1.metric("Interested", stats.get("interested", 0))
col2.metric("In progress", stats.get("in_progress", 0))
col3.metric("Completed", stats.get("completed", 0))

st.divider()

st.markdown("Go to the **Courses** page to browse and update your status.")
