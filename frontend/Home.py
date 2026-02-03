from datetime import datetime
from pathlib import Path
import sys

import pandas as pd
import streamlit as st


sys.path.append(str(Path(__file__).parent))

from services.auth import load_role, logout as api_logout
from services.courses import load_courses
from services.paths import load_path, load_paths, load_selected_paths
from services.tracking import load_recent_activity, load_stats, load_team_recent_activity, load_tracking, load_user_stats
from state.session import get_email, logout, require_login
from ui.style import apply_global_style


def _format_time(ts: str) -> str:
    if not ts:
        return ""
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y %H:%M")
    except ValueError:
        return ts


st.set_page_config(page_title="Home", layout="wide")
apply_global_style()

require_login()
email = get_email()
st.sidebar.caption(f"Signed in as {email}")
if st.sidebar.button("Log out"):
    try:
        api_logout()
    except Exception:
        pass
    logout()
    st.switch_page("pages/Login.py")

st.title("Dashboard")
st.caption("Your learning overview and recent activity.")

courses_df, load_error = load_courses()
if load_error:
    st.error(load_error)

paths, _ = load_paths()
role = load_role()

st.subheader("Progress snapshot")
mode = "My stats"
if role == "admin":
    mode = st.radio("Snapshot mode", ["My stats", "Team totals"], horizontal=True)

col1, col2, col3 = st.columns(3)
stats = load_stats(
    "" if role == "admin" and mode == "Team totals" else email.strip(),
    role == "admin" and mode == "Team totals",
)
col1.metric("Interested", stats.get("interested", 0))
col2.metric("In progress", stats.get("in_progress", 0))
col3.metric("Completed", stats.get("completed", 0))

st.divider()

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

st.subheader("My path progress")
my_paths = load_selected_paths()
if not my_paths:
    st.caption("No paths selected yet.")
else:
    for path in my_paths:
        path_id = path.get("id")
        if not path_id:
            continue
        path_detail, path_error = load_path(path_id)
        if path_error or not path_detail:
            continue

        courses = path_detail.get("courses", [])
        total = len(courses)
        completed = sum(1 for course in courses if tracking_map.get(int(course.get("id", 0)), "") == "completed")
        in_progress = sum(1 for course in courses if tracking_map.get(int(course.get("id", 0)), "") == "in_progress")
        interested = sum(1 for course in courses if tracking_map.get(int(course.get("id", 0)), "") == "interested")
        progress = completed / total if total else 0

        st.markdown(f"**{path_detail.get('name', '(untitled path)')}**")
        st.progress(progress)
        st.caption(f"Progress: {completed}/{total} completed • In progress: {in_progress} • Interested: {interested}")

st.divider()

st.subheader("Recent activity")
activity = load_recent_activity(email.strip(), limit=3)
if not activity:
    st.caption("No recent updates yet.")
else:
    course_lookup = {int(row["id"]): row["title"] for _, row in courses_df.iterrows() if row.get("id")}

    for item in activity:
        cid = int(item.get("course_id", 0))
        title = course_lookup.get(cid, f"Course {cid}")
        status = item.get("status", "")
        updated = _format_time(item.get("updated_at", ""))
        st.write(f"• {title} — {status} ({updated})")

st.divider()

if role == "admin":
    st.subheader("Team stats by user")
    user_stats = load_user_stats()
    if not user_stats:
        st.info("No user stats yet.")
    else:
        st.dataframe(user_stats)

    st.subheader("Team recent activity")
    team_activity = load_team_recent_activity(limit=5)
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

    st.divider()

st.subheader("Featured paths")
if not paths:
    st.info("No paths yet. Create one on the Paths page.")
else:
    for path in paths[:3]:
        st.page_link("pages/Paths.py", label=path.get("name", "(untitled path)"))
        if path.get("description"):
            st.write(path["description"])
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
