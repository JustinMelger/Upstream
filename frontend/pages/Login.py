from pathlib import Path
import sys
import os

import streamlit as st


sys.path.append(str(Path(__file__).resolve().parents[1]))

from state.session import login, is_authenticated
from ui.style import apply_global_style


st.set_page_config(page_title="Login", layout="wide")
apply_global_style()

if is_authenticated():
    st.switch_page("Home.py")

st.title("Login")
st.caption("Sign in to access your learning hub.")

email = st.text_input("Email", "")
invite_code = st.text_input("Invite code", type="password")
submitted = st.button("Sign in")

required_code = os.getenv("INVITE_CODE", "").strip()

if submitted:
    if not email.strip():
        st.error("Email is required.")
    elif required_code and invite_code.strip() != required_code:
        st.error("Invalid invite code.")
    else:
        login(email.strip())
        st.success("Signed in.")
        st.rerun()
