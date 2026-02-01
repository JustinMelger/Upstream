import streamlit as st


def get_email() -> str:
    return st.session_state.get("colleague_email", "")


def set_email(value: str) -> None:
    st.session_state["colleague_email"] = value
