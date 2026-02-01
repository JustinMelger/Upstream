import sys
from pathlib import Path

import pandas as pd
import streamlit as st
from datetime import datetime

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ui.style import apply_global_style
from services.auth import load_role
from services.courses import load_courses
from services.tracking import (
    load_recent_activity,
    load_stats,
    load_team_recent_activity,
    load_tracking,
    load_user_stats,
)

st.set_page_config(page_title="Overview", page_icon="📚", layout="wide")
apply_global_style()

st.title("Overview")
st.caption("Overview of courses and progress.")

courses_df, load_error = load_courses()
if load_error:
    st.error(load_error)

st.subheader("Progress snapshot")
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

st.divider()

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

    _render_course_list("Interested", interested_ids)
    _render_course_list("In progress", in_progress_ids)
    _render_course_list("Completed", completed_ids)

    st.divider()

    st.subheader("Recent activity")
    activity = load_recent_activity(email.strip(), limit=3)
    if not activity:
        st.caption("No recent updates yet.")
    else:
        course_lookup = {int(row["id"]): row["title"] for _, row in courses_df.iterrows() if row.get("id")}

        def _format_time(ts: str) -> str:
            if not ts:
                return ""
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                return dt.strftime("%b %d, %Y %H:%M")
            except ValueError:
                return ts

        for item in activity:
            cid = int(item.get("course_id", 0))
            title = course_lookup.get(cid, f"Course {cid}")
            status = item.get("status", "")
            updated = _format_time(item.get("updated_at", ""))
            st.write(f"• {title} — {status} ({updated})")

st.divider()

if role == "admin":
    st.divider()
    st.subheader("Team stats by user")
    user_stats = load_user_stats(email.strip())
    if not user_stats:
        st.info("No user stats yet.")
    else:
        st.dataframe(user_stats)

    st.subheader("Team recent activity")
    team_activity = load_team_recent_activity(email.strip(), limit=5)
    if not team_activity:
        st.info("No team activity yet.")
    else:
        course_lookup = {int(row["id"]): row["title"] for _, row in courses_df.iterrows() if row.get("id")}
        for item in team_activity:
            cid = int(item.get("course_id", 0))
            title = course_lookup.get(cid, f"Course {cid}")
            status = item.get("status", "")
            updated = _format_time(item.get("updated_at", ""))
            who = item.get("colleague_id", "someone")
            st.write(f"• {who}: {title} — {status} ({updated})")
