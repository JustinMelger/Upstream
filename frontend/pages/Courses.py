from pathlib import Path
import sys

import pandas as pd
import streamlit as st


sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.auth import load_role
from services.courses import add_course, delete_course, load_courses, update_course
from services.tracking import delete_status, load_tracking, save_status
from state.session import get_email, logout, require_login
from ui.components import hero_header
from ui.style import apply_global_style


st.set_page_config(page_title="Learning Hub", layout="wide")
apply_global_style()

require_login()
email = get_email()


def render_sidebar(df: pd.DataFrame) -> tuple[str, str, str, list, list, list]:
    st.sidebar.header("Filters")
    st.sidebar.caption(f"Signed in as {email}")
    if st.sidebar.button("Log out"):
        logout()
        st.switch_page("pages/Login.py")
    role = load_role(email.strip())

    search = st.sidebar.text_input("Search", "")
    category = st.sidebar.multiselect("Category", sorted([c for c in df["category"].unique() if c]))
    provider = st.sidebar.multiselect("Provider", sorted([p for p in df["provider"].unique() if p]))
    level = st.sidebar.multiselect("Level", sorted([l for l in df["level"].unique() if l]))

    if role == "admin":
        st.sidebar.caption("Admin mode enabled.")

    return email.strip(), role, search, category, provider, level


def filter_courses(df: pd.DataFrame, search: str, category: list, provider: list, level: list) -> pd.DataFrame:
    filtered = df.copy()

    if search.strip():
        s = search.strip().lower()
        filtered = filtered[
            filtered.apply(
                lambda r: s in (r["title"] + " " + r["category"] + " " + r["provider"]).lower(),
                axis=1,
            )
        ]

    if category:
        filtered = filtered[filtered["category"].isin(category)]
    if provider:
        filtered = filtered[filtered["provider"].isin(provider)]
    if level:
        filtered = filtered[filtered["level"].isin(level)]

    return filtered


def render_course_card(row: pd.Series, email: str, role: str, tracking_map: dict) -> None:
    with st.container(border=True):
        col1, col2 = st.columns([5, 1])

        with col1:
            if role == "admin" and int(row.get("id", 0) or 0):
                course_id = int(row.get("id", 0) or 0)
                with st.expander("Edit course"):
                    with st.form(f"edit_course_{course_id}"):
                        edit_title = st.text_input("Title*", value=row.get("title") or "")
                        edit_provider = st.text_input("Provider", value=row.get("provider") or "")
                        edit_category = st.text_input("Category", value=row.get("category") or "")
                        edit_level = st.selectbox(
                            "Level",
                            ["", "Beginner", "Intermediate", "Advanced"],
                            index=["", "Beginner", "Intermediate", "Advanced"].index(row.get("level") or ""),
                        )
                        edit_duration = st.number_input(
                            "Duration (hours)",
                            min_value=0.0,
                            step=0.5,
                            value=float(row.get("duration_hours") or 0.0),
                        )
                        edit_url = st.text_input("URL", value=row.get("url") or "")
                        submitted = st.form_submit_button("Save changes")

                    if submitted:
                        if not edit_title.strip():
                            st.error("Title is required.")
                        else:
                            try:
                                response = update_course(
                                    course_id,
                                    {
                                        "title": edit_title.strip(),
                                        "provider": edit_provider.strip(),
                                        "category": edit_category.strip(),
                                        "level": edit_level.strip(),
                                        "duration_hours": edit_duration if edit_duration > 0 else None,
                                        "url": edit_url.strip(),
                                    },
                                    email,
                                )
                                response.raise_for_status()
                                st.success("Course updated.")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception:
                                st.error("Could not update course.")

            title = row["title"] or "(untitled)"
            st.subheader(title)

            pills = []
            if row.get("provider"):
                pills.append(f"<span class='pill'>🏢 {row['provider']}</span>")
            if row.get("category"):
                pills.append(f"<span class='pill alt'>🏷️ {row['category']}</span>")
            if row.get("level"):
                pills.append(f"<span class='pill'>🎯 {row['level']}</span>")
            if pills:
                st.markdown("".join(pills), unsafe_allow_html=True)

            meta = []
            if pd.notna(row.get("duration_hours")):
                meta.append(f"⏱ {row['duration_hours']} hours")
            if meta:
                st.caption(" • ".join(meta))

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
            if course_id:
                if course_id in tracking_map:
                    st.caption("In My Courses")
                    if st.button("Remove", key=f"remove_mycourse_{course_id}"):
                        if not email:
                            st.warning("Enter your name/email in the sidebar first.")
                        else:
                            try:
                                response = delete_status(email, course_id)
                                response.raise_for_status()
                                st.success("Removed from My Courses.")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception:
                                st.error("Could not remove course.")
                else:
                    if st.button("Add to My Courses", key=f"add_mycourse_{course_id}"):
                        if not email:
                            st.warning("Enter your name/email in the sidebar first.")
                        else:
                            try:
                                response = save_status(email, course_id, "interested")
                                response.raise_for_status()
                                st.success("Added to My Courses.")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception:
                                st.error("Could not add course.")

            if role == "admin" and course_id:
                confirm = st.checkbox("Confirm delete", key=f"confirm_delete_{course_id}")
                if st.button("Delete course", key=f"delete_{course_id}"):
                    if not confirm:
                        st.warning("Check confirm before deleting.")
                    else:
                        try:
                            response = delete_course(course_id, email)
                            response.raise_for_status()
                            st.success("Course deleted.")
                            st.cache_data.clear()
                            st.rerun()
                        except Exception:
                            st.error("Could not delete course.")


def render_add_course(role: str, email: str) -> None:
    with st.expander("➕ Add a course"):
        if role != "admin":
            st.info("Read-only mode. Admins can add or edit courses.")
            return

        with st.form("add_course"):
            t = st.text_input("Title*")
            p = st.text_input("Provider (Udemy/Coursera/etc.)")
            c = st.text_input("Category")
            l = st.selectbox("Level", ["", "Beginner", "Intermediate", "Advanced"])
            d = st.number_input("Duration (hours)", min_value=0.0, step=0.5)
            u = st.text_input("URL")
            submitted = st.form_submit_button("Add course")

        if submitted:
            if not t.strip():
                st.error("Title is required.")
                return

            try:
                response = add_course(
                    {
                        "title": t.strip(),
                        "provider": p.strip(),
                        "category": c.strip(),
                        "level": l.strip(),
                        "duration_hours": d if d > 0 else None,
                        "url": u.strip(),
                    },
                    email,
                )
                response.raise_for_status()
                st.success("Course added.")
                st.cache_data.clear()
                st.rerun()
            except Exception:
                st.error("Could not add course.")


courses_df, load_error = load_courses()
if load_error:
    st.error(load_error)

hero_header(courses_df)
st.divider()

email, role, search, category, provider, level = render_sidebar(courses_df)
tracking_map = load_tracking(email)

filtered = filter_courses(courses_df, search, category, provider, level)

st.markdown(
    f"Showing {len(filtered)} of {len(courses_df)} courses",
)

for _, row in filtered.iterrows():
    render_course_card(row, email, role, tracking_map)
    st.divider()

st.divider()
render_add_course(role, email)
