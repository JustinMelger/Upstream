from pathlib import Path
import sys

import pandas as pd
import streamlit as st


sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.courses import load_courses
from services.tracking import delete_status, load_tracking, save_status
from ui.style import apply_global_style
from state.session import get_email, logout, require_login


st.set_page_config(page_title="My Courses", layout="wide")
apply_global_style()

require_login()

st.title("My Courses")
st.caption("Your tracked courses and current status.")

email = get_email()
st.sidebar.caption(f"Signed in as {email}")
if st.sidebar.button("Log out"):
    logout()
    st.switch_page("pages/Login.py")

courses_df, load_error = load_courses()
if load_error:
    st.error(load_error)

tracking_map = load_tracking(email.strip())
if not tracking_map:
    st.info("No tracked courses yet. Set a status on the Courses page.")
    st.stop()

filtered = courses_df[courses_df["id"].isin(tracking_map.keys())].copy()
if filtered.empty:
    st.info("No tracked courses yet. Set a status on the Courses page.")
    st.stop()

filtered["status"] = filtered["id"].apply(lambda cid: tracking_map.get(int(cid), ""))
status_order = {"interested": 0, "in_progress": 1, "completed": 2, "": 3}
filtered["status_sort"] = filtered["status"].map(lambda s: status_order.get(s, 99))
filtered = filtered.sort_values(["status_sort", "title"]).drop(columns=["status_sort"])

st.caption(f"You have {len(filtered)} tracked courses.")

for _, row in filtered.iterrows():
    with st.container(border=True):
        col1, col2 = st.columns([5, 1])

        with col1:
            title = row.get("title") or "(untitled)"
            st.subheader(title)
            meta = []
            if row.get("provider"):
                meta.append(f"🏢 {row['provider']}")
            if row.get("category"):
                meta.append(f"🏷️ {row['category']}")
            if row.get("level"):
                meta.append(f"🎯 {row['level']}")
            if meta:
                st.caption(" • ".join(meta))

            if pd.notna(row.get("duration_hours")):
                st.caption(f"⏱ {row['duration_hours']} hours")

            if row.get("url"):
                st.write(row["url"])
            else:
                st.warning("Missing URL")

        with col2:
            if row.get("url"):
                try:
                    st.link_button("Open", row["url"])
                except Exception:
                    st.markdown(f"[Open]({row['url']})")

            course_id = int(row.get("id", 0) or 0)
            current_status = tracking_map.get(course_id, "")
            status = st.selectbox(
                "Status",
                ["", "interested", "in_progress", "completed"],
                index=["", "interested", "in_progress", "completed"].index(current_status or ""),
                key=f"mycourses_status_{course_id}",
            )
            if status != current_status:
                try:
                    response = save_status(email.strip(), course_id, status)
                    response.raise_for_status()
                    st.success("Status saved.")
                    st.cache_data.clear()
                    st.rerun()
                except Exception:
                    st.error("Could not save status.")

            if st.button("Remove", key=f"mycourses_remove_{course_id}"):
                try:
                    response = delete_status(email.strip(), course_id)
                    response.raise_for_status()
                    st.success("Removed from My Courses.")
                    st.cache_data.clear()
                    st.rerun()
                except Exception:
                    st.error("Could not remove course.")
