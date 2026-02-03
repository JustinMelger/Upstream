from pathlib import Path
import sys

import streamlit as st


sys.path.append(str(Path(__file__).resolve().parents[1]))

from services.auth import login as api_login
from state.session import is_authenticated, set_email, set_token
from ui.style import apply_global_style


st.set_page_config(page_title="Login", layout="wide")
apply_global_style()

if is_authenticated():
    st.switch_page("Home.py")

st.title("Login")
st.caption("Sign in to access your learning hub.")

username = st.text_input("Username", "")
password = st.text_input("Password", type="password")
submitted = st.button("Sign in")

if submitted:
    if not username.strip() or not password.strip():
        st.error("Username and password are required.")
    else:
        try:
            response = api_login(username.strip(), password.strip())
            if response.status_code == 401:
                st.error("Invalid credentials.")
            else:
                response.raise_for_status()
                data = response.json()
                set_email(data.get("username", username.strip()))
                set_token(data.get("token", ""))
                st.success("Signed in.")
                st.rerun()
        except Exception:
            st.error("Could not sign in.")
