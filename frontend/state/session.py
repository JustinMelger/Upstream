import os

from services.auth import get_me
import streamlit as st


COOKIE_NAME = "lh_session"


def get_email() -> str:
    return st.session_state.get("colleague_email", "")


def set_email(value: str) -> None:
    st.session_state["colleague_email"] = value


def is_authenticated() -> bool:
    return bool(get_token())


def _set_cookie(value: str) -> None:
    setter = getattr(st, "experimental_set_cookie", None) or getattr(st, "set_cookie", None)
    if setter:
        secure = os.getenv("COOKIE_SECURE", "true").lower() == "true"
        setter(COOKIE_NAME, value, max_age=60 * 60 * 24 * 30, secure=secure, httponly=True, samesite="Lax")


def _get_cookie() -> str:
    getter = getattr(st, "experimental_get_cookie", None) or getattr(st, "get_cookie", None)
    if getter:
        return getter(COOKIE_NAME) or ""
    return ""


def get_token() -> str:
    token = st.session_state.get("session_token", "")
    if token:
        return token
    token = _get_cookie()
    if token:
        st.session_state["session_token"] = token
    return token


def login(email: str) -> None:
    st.session_state["is_authenticated"] = True
    set_email(email)


def set_token(token: str) -> None:
    st.session_state["session_token"] = token
    _set_cookie(token)


def logout(clear_cookie: bool = True) -> None:
    st.session_state["is_authenticated"] = False
    st.session_state["colleague_email"] = ""
    st.session_state["session_token"] = ""
    if clear_cookie:
        _set_cookie("")


def require_login() -> None:
    token = get_token()
    if not token:
        st.switch_page("pages/Login.py")
    if not st.session_state.get("colleague_email"):
        try:
            response = get_me(token)
            response.raise_for_status()
            data = response.json()
            set_email(data.get("username", ""))
        except Exception:
            logout()
            st.switch_page("pages/Login.py")
