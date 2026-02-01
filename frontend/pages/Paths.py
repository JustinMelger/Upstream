import sys
from pathlib import Path
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ui.style import apply_global_style
from services.auth import load_role
from services.courses import load_courses
from services.paths import add_path, delete_path, load_path, load_paths

st.set_page_config(page_title="Learning Paths", page_icon="🧭", layout="wide")
apply_global_style()

st.title("🧭 Learning Paths")
st.caption("Curated paths to guide learning journeys.")

email = st.sidebar.text_input("Your name or email", "")
role = load_role(email.strip())

paths, load_error = load_paths()
if load_error:
    st.error(load_error)

if not paths:
    st.info("No learning paths yet. Admins can add these later.")
else:
    path_options = {p["name"]: p["id"] for p in paths}
    selected_name = st.selectbox("Select a path", [""] + list(path_options.keys()))
    if selected_name:
        path_id = path_options[selected_name]
        path_detail, path_error = load_path(path_id)
        if path_error:
            st.error(path_error)
        elif path_detail:
            st.subheader(path_detail.get("name", "(untitled path)"))
            if path_detail.get("description"):
                st.write(path_detail["description"])

            courses = path_detail.get("courses", [])
            if not courses:
                st.info("No courses in this path yet.")
            else:
                st.markdown("**Courses in this path**")
                for course in courses:
                    st.write(f"• {course.get('title', '(untitled)')}")

            if role == "admin":
                confirm = st.checkbox("Confirm delete path", key=f"confirm_delete_path_{path_id}")
                if st.button("Delete path", key=f"delete_path_{path_id}"):
                    if not confirm:
                        st.warning("Check confirm before deleting.")
                    else:
                        try:
                            response = delete_path(path_id, email.strip())
                            response.raise_for_status()
                            st.success("Path deleted.")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception:
                            st.error("Could not delete path.")

with st.expander("➕ Create a path"):
    if role != "admin":
        st.info("Read-only mode. Admins can create paths.")
    else:
        courses_df, _ = load_courses()
        options = [
            (int(row["id"]), f"{row['title']} ({row['provider']})".strip())
            for _, row in courses_df.iterrows()
        ]
        course_labels = [label for _, label in options]
        selected_labels = st.multiselect("Select courses", course_labels)
        selected_ids = [options[course_labels.index(label)][0] for label in selected_labels]

        name = st.text_input("Path name*")
        description = st.text_area("Description")
        submitted = st.button("Create path")

        if submitted:
            if not name.strip():
                st.error("Path name is required.")
            else:
                try:
                    response = add_path(
                        {
                            "name": name.strip(),
                            "description": description.strip(),
                            "course_ids": selected_ids,
                        },
                        email.strip(),
                    )
                    if response.status_code == 409:
                        st.error("A path with that name already exists.")
                    else:
                        response.raise_for_status()
                        st.success("Path created.")
                        st.cache_data.clear()
                        st.rerun()
                except Exception:
                    st.error("Could not create path.")
