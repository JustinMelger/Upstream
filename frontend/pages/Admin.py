from datetime import datetime
from pathlib import Path
import sys

import streamlit as st


sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.auth import (
    create_user,
    delete_user,
    list_users,
    load_role,
    logout as api_logout,
    reset_password,
    set_user_disabled,
)
from state.session import get_email, logout, require_login
from ui.style import apply_global_style


st.set_page_config(page_title="Admin", layout="wide")
apply_global_style()

require_login()
username = get_email()
st.sidebar.caption(f"Signed in as {username}")
if st.sidebar.button("Log out"):
    try:
        api_logout()
    except Exception:
        pass
    logout()
    st.switch_page("pages/Login.py")

role = load_role()
if role != "admin":
    st.error("Admin access required.")
    st.stop()

st.title("Admin")
st.caption("Manage users and admin settings.")

st.subheader("Create user")
with st.form("create_user"):
    new_username = st.text_input("Username")
    new_password = st.text_input("Password", type="password")
    new_role = st.selectbox("Role", ["user", "admin"])
    submitted = st.form_submit_button("Create user")

if submitted:
    if not new_username.strip() or not new_password.strip():
        st.error("Username and password are required.")
    else:
        try:
            response = create_user(new_username.strip(), new_password.strip(), new_role)
            if response.status_code == 409:
                st.error("User already exists.")
            else:
                response.raise_for_status()
                st.success("User created.")
                st.rerun()
        except Exception:
            st.error("Could not create user.")

st.divider()

st.subheader("User list")
users = list_users()
if not users:
    st.caption("No users found.")
else:
    search = st.text_input("Search users", "", key="user_search")
    search_lower = search.strip().lower()
    if search_lower:
        users = [
            user
            for user in users
            if search_lower in user.get("username", "").lower() or search_lower in user.get("role", "").lower()
        ]

    def _format_time(ts: str) -> str:
        if not ts:
            return ""
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            return dt.strftime("%b %d, %Y %H:%M")
        except ValueError:
            return ts

    formatted = []
    for row in users:
        formatted.append(
            {
                "Username": row.get("username", ""),
                "Role": row.get("role", ""),
                "Created at": _format_time(row.get("created_at", "")),
                "Updated at": _format_time(row.get("updated_at", "")),
                "Last login": _format_time(row.get("last_login_at", "")),
                "Disabled": "Yes" if row.get("disabled") else "No",
            }
        )
    st.dataframe(formatted, width="stretch", hide_index=True)

st.subheader("Reset password")
with st.form("reset_password"):
    reset_username = st.text_input("Username", key="reset_username")
    reset_password_value = st.text_input("New password", type="password", key="reset_password")
    reset_submit = st.form_submit_button("Reset password")

if reset_submit:
    if not reset_username.strip() or not reset_password_value.strip():
        st.error("Username and new password are required.")
    else:
        try:
            response = reset_password(reset_username.strip(), reset_password_value.strip())
            if response.status_code == 404:
                st.error("User not found.")
            else:
                response.raise_for_status()
                st.success("Password updated.")
                st.rerun()
        except Exception:
            st.error("Could not reset password.")

st.subheader("Delete user")
with st.form("delete_user"):
    delete_username = st.text_input("Username", key="delete_username")
    confirm_delete = st.checkbox("Confirm delete")
    delete_submit = st.form_submit_button("Delete user")

if delete_submit:
    if not delete_username.strip():
        st.error("Username is required.")
    elif not confirm_delete:
        st.error("Confirm delete to continue.")
    else:
        try:
            response = delete_user(delete_username.strip())
            if response.status_code == 404:
                st.error("User not found.")
            else:
                response.raise_for_status()
                st.success("User deleted.")
                st.rerun()
        except Exception:
            st.error("Could not delete user.")

st.subheader("Disable user")
with st.form("disable_user"):
    disable_username = st.text_input("Username", key="disable_username")
    disable_action = st.selectbox("Action", ["Disable", "Enable"])
    disable_submit = st.form_submit_button("Update status")

if disable_submit:
    if not disable_username.strip():
        st.error("Username is required.")
    else:
        try:
            response = set_user_disabled(disable_username.strip(), disable_action == "Disable")
            if response.status_code == 404:
                st.error("User not found.")
            else:
                response.raise_for_status()
                st.success("User updated.")
                st.rerun()
        except Exception:
            st.error("Could not update user.")
