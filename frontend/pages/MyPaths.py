from pathlib import Path
import sys

import streamlit as st


sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.paths import load_path, load_selected_paths, unselect_path
from services.tracking import load_tracking, save_status
from ui.style import apply_global_style


st.set_page_config(page_title="My Paths", page_icon="🧭", layout="wide")
apply_global_style()

st.title("My Paths")
st.caption("Update course status and manage your selected learning paths.")

email = st.sidebar.text_input("Your name or email", "")

if not email.strip():
    st.info("Enter your name or email in the sidebar to view your paths.")
    st.stop()

tracking_map = load_tracking(email.strip())
my_paths = load_selected_paths(email.strip())

if not my_paths:
    st.info("No paths selected yet. Add one on the Learning Paths page.")
    st.stop()

st.caption(f"You have {len(my_paths)} selected paths.")

for path in my_paths:
    path_id = path.get("id")
    if not path_id:
        continue
    path_detail, path_error = load_path(path_id)
    if path_error:
        st.error(path_error)
        continue
    if not path_detail:
        continue

    with st.container(border=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.subheader(path_detail.get("name", "(untitled path)"))
            if path_detail.get("description"):
                st.write(path_detail["description"])

            courses = path_detail.get("courses", [])
            if not courses:
                st.info("No courses in this path yet.")
            else:
                total = len(courses)
                completed = sum(
                    1 for course in courses if tracking_map.get(int(course.get("id", 0)), "") == "completed"
                )
                in_progress = sum(
                    1
                    for course in courses
                    if tracking_map.get(int(course.get("id", 0)), "") == "in_progress"
                )
                interested = sum(
                    1 for course in courses if tracking_map.get(int(course.get("id", 0)), "") == "interested"
                )
                progress = completed / total if total else 0
                st.progress(progress)
                st.caption(
                    f"Progress: {completed}/{total} completed • In progress: {in_progress} • Interested: {interested}"
                )
                st.markdown("**Courses in this path**")
                for idx, course in enumerate(courses, start=1):
                    title = course.get("title", "(untitled)")
                    url = course.get("url", "")
                    course_id = course.get("id")
                    row = st.columns([0.6, 5.4, 2])
                    with row[0]:
                        st.markdown(f"**{idx}.**")
                    with row[1]:
                        if url:
                            try:
                                st.link_button(title, url)
                            except Exception:
                                st.markdown(f"[{title}]({url})")
                        else:
                            st.write(f"• {title}")
                    with row[2]:
                        if course_id:
                            current_status = tracking_map.get(int(course_id), "")
                            status = st.selectbox(
                                "Status",
                                ["", "interested", "in_progress", "completed"],
                                index=["", "interested", "in_progress", "completed"].index(current_status or ""),
                                key=f"mypath_course_status_{path_id}_{course_id}",
                                label_visibility="collapsed",
                            )
                            if status != current_status:
                                try:
                                    response = save_status(email.strip(), int(course_id), status)
                                    response.raise_for_status()
                                    st.success("Status saved.")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception:
                                    st.error("Could not save status.")

        with col2:
            if st.button("Remove path", key=f"mypath_remove_{path_id}"):
                try:
                    response = unselect_path(path_id, email.strip())
                    response.raise_for_status()
                    st.success("Path removed.")
                    st.cache_data.clear()
                    st.rerun()
                except Exception:
                    st.error("Could not remove path.")

    st.divider()
