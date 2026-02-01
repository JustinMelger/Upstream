import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ui.style import apply_global_style
from services.auth import load_role
from services.courses import load_courses
from services.tracking import load_stats, load_tracking, load_user_stats

st.set_page_config(page_title="Overview", page_icon="📚", layout="wide")
apply_global_style()

st.title("Overview")
st.caption("Overview of courses and progress.")

courses_df, load_error = load_courses()
if load_error:
    st.error(load_error)

st.subheader("📈 Progress snapshot")
email = st.text_input("Your name or email", "")
role = load_role(email.strip())
mode = "My stats"
if role == "admin":
    mode = st.radio("Snapshot mode", ["My stats", "Team totals"], horizontal=True)

col1, col2, col3 = st.columns(3)

stats = load_stats(
    email.strip(),
    email.strip(),
    role == "admin" and mode == "Team totals",
)

col1.metric("Interested", stats.get("interested", 0))
col2.metric("In progress", stats.get("in_progress", 0))
col3.metric("Completed", stats.get("completed", 0))

if not email.strip():
    st.info("Enter your email above to see your personal course list.")
else:
    tracking_map = load_tracking(email.strip())

    interested_ids = [cid for cid, status in tracking_map.items() if status == "interested"]
    in_progress_ids = [cid for cid, status in tracking_map.items() if status == "in_progress"]
    completed_ids = [cid for cid, status in tracking_map.items() if status == "completed"]

    def _render_course_list(title: str, ids: list[int]):
        st.subheader(title)
        if not ids:
            st.caption("No courses yet.")
            return
        subset = courses_df[courses_df["id"].isin(ids)]
        for _, row in subset.iterrows():
            st.write(f"• {row['title']}")

    _render_course_list("⭐ Interested", interested_ids)
    _render_course_list("🚧 In progress", in_progress_ids)
    _render_course_list("✅ Completed", completed_ids)

st.markdown("Go to the **Courses** page to browse and update your status.")

if role == "admin":
    st.subheader("👥 Team stats by user")
    user_stats = load_user_stats(email.strip())
    if not user_stats:
        st.info("No user stats yet.")
    else:
        st.dataframe(user_stats, use_container_width=True)
