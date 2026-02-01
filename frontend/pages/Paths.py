from pathlib import Path
import sys

import streamlit as st


sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.auth import load_role
from services.courses import load_courses
from services.paths import (
    add_path,
    delete_path,
    load_path,
    load_paths,
    load_selected_paths,
    select_path,
    unselect_path,
    update_path,
)
from ui.style import apply_global_style


st.set_page_config(page_title="Learning Paths", page_icon="🧭", layout="wide")
apply_global_style()

st.title("Learning Paths")
st.caption("Curated paths to guide learning journeys.")

def _format_course_label(row) -> str:
    title = row.get("title") or "(untitled)"
    provider = row.get("provider") or ""
    category = row.get("category") or ""
    level = row.get("level") or ""
    meta = " - ".join([item for item in [provider, category, level] if item])
    label = f"{title} ({meta})" if meta else title
    return label[:120]


def _course_selector(options: list[tuple[int, str]], selected_ids: set[int], key_prefix: str) -> list[int]:
    search = st.text_input("Search courses", "", key=f"{key_prefix}_search")
    search_lower = search.strip().lower()
    filtered = options
    if search_lower:
        filtered = [item for item in options if search_lower in item[1].lower()]

    selected = set(selected_ids)
    for course_id, label in filtered:
        checked = course_id in selected
        if st.checkbox(label, value=checked, key=f"{key_prefix}_course_{course_id}"):
            selected.add(course_id)
        else:
            selected.discard(course_id)

    return list(selected)

email = st.sidebar.text_input("Your name or email", "")
role = load_role(email.strip())

my_paths = []
if email.strip():
    st.sidebar.subheader("My paths")
    my_paths = load_selected_paths(email.strip())
    if not my_paths:
        st.sidebar.caption("No paths selected.")
    else:
        for p in my_paths:
            label = p.get("name", "(untitled path)")
            col1, col2 = st.sidebar.columns([4, 1])
            if col1.button(label, key=f"sidebar_path_{p.get('id', label)}"):
                st.session_state["selected_path_name"] = label
                st.switch_page("pages/MyPaths.py")
            if col2.button("✕", key=f"sidebar_unselect_{p.get('id', label)}"):
                try:
                    response = unselect_path(p.get("id"), email.strip())
                    response.raise_for_status()
                    st.success("Path removed.")
                    st.cache_data.clear()
                    st.rerun()
                except Exception:
                    st.error("Could not remove path.")

selected_path_ids = {p.get("id") for p in my_paths if p.get("id") is not None}

paths, load_error = load_paths()
if load_error:
    st.error(load_error)

if not paths:
    st.info("No learning paths yet. Admins can add these later.")
else:
    path_options = {p["name"]: p["id"] for p in paths}
    if st.session_state.get("selected_path_name") not in path_options:
        st.session_state.pop("selected_path_name", None)
    selected_name = st.session_state.get("selected_path_name", "")

    if selected_name:
        st.caption(f"Showing 1 of {len(paths)} paths (filtered by sidebar selection).")
        if st.button("Clear selection"):
            st.session_state.pop("selected_path_name", None)
            st.rerun()
        paths_to_render = [p for p in paths if p.get("name") == selected_name]
    else:
        st.caption(f"Showing {len(paths)} paths.")
        paths_to_render = paths

    for path in paths_to_render:
        path_id = path.get("id")
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
                if role == "admin":
                    with st.expander("Edit path"):
                        courses_df, _ = load_courses()
                        options = [(int(row["id"]), _format_course_label(row)) for _, row in courses_df.iterrows()]
                        selected_ids = {course.get("id") for course in path_detail.get("courses", []) if course.get("id")}

                        with st.form(f"edit_path_{path_id}"):
                            edit_name = st.text_input(
                                "Path name*",
                                value=path_detail.get("name", ""),
                            )
                            edit_description = st.text_area(
                                "Description",
                                value=path_detail.get("description", ""),
                            )
                            edit_selected_ids = _course_selector(
                                options,
                                selected_ids,
                                key_prefix=f"edit_path_{path_id}",
                            )
                            submitted = st.form_submit_button("Save changes")

                        if submitted:
                            cleaned_name = edit_name.strip()
                            if cleaned_name:
                                cleaned_name = cleaned_name[:1].upper() + cleaned_name[1:]
                            if not cleaned_name:
                                st.error("Path name is required.")
                            else:
                                try:
                                    response = update_path(
                                        path_id,
                                        {
                                            "name": cleaned_name,
                                            "description": edit_description.strip(),
                                            "course_ids": edit_selected_ids,
                                        },
                                        email.strip(),
                                    )
                                    if response.status_code == 409:
                                        st.error("A path with that name already exists.")
                                    else:
                                        response.raise_for_status()
                                        st.success("Path updated.")
                                        st.cache_data.clear()
                                        st.rerun()
                                except Exception:
                                    st.error("Could not update path.")

                        st.markdown("---")
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

                if not courses:
                    st.info("No courses in this path yet.")
                else:
                    st.markdown("**Courses in this path**")
                    if not email.strip():
                        st.caption("Enter your name/email in the sidebar to track course status.")
                    for course in courses:
                        title = course.get("title", "(untitled)")
                        url = course.get("url", "")
                        if url:
                            try:
                                st.link_button(title, url)
                            except Exception:
                                st.markdown(f"[{title}]({url})")
                        else:
                            st.write(f"• {title}")

            with col2:
                if email.strip():
                    if path_id in selected_path_ids:
                        if st.button("Remove from my paths", key=f"remove_path_{path_id}"):
                            try:
                                response = unselect_path(path_id, email.strip())
                                response.raise_for_status()
                                st.success("Path removed.")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception:
                                st.error("Could not remove path.")
                    else:
                        if st.button("Add to my paths", key=f"add_path_{path_id}"):
                            try:
                                response = select_path(path_id, email.strip())
                                response.raise_for_status()
                                st.success("Path added.")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception:
                                st.error("Could not add path.")
                else:
                    st.caption("Enter your name/email in the sidebar to save.")


        st.divider()

with st.expander("➕ Create a path"):
    if role != "admin":
        st.info("Read-only mode. Admins can create paths.")
    else:
        courses_df, _ = load_courses()
        options = [(int(row["id"]), _format_course_label(row)) for _, row in courses_df.iterrows()]
        selected_ids = _course_selector(options, set(), key_prefix="create_path")

        name = st.text_input("Path name*")
        description = st.text_area("Description")
        submitted = st.button("Create path")

        if submitted:
            cleaned_name = name.strip()
            if cleaned_name:
                cleaned_name = cleaned_name[:1].upper() + cleaned_name[1:]
            if not cleaned_name:
                st.error("Path name is required.")
            else:
                try:
                    response = add_path(
                        {
                            "name": cleaned_name,
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
