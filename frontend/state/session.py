import streamlit as st


def get_email() -> str:
    return st.session_state.get("colleague_email", "")


def set_email(value: str) -> None:
    st.session_state["colleague_email"] = value


def is_authenticated() -> bool:
    return bool(st.session_state.get("is_authenticated"))


def login(email: str) -> None:
    st.session_state["is_authenticated"] = True
    set_email(email)


def logout() -> None:
    st.session_state["is_authenticated"] = False
    st.session_state["colleague_email"] = ""


def require_login() -> None:
    if not is_authenticated():
        st.switch_page("pages/Login.py")
