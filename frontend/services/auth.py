from services.api import get
import streamlit as st


@st.cache_data
def load_role(email: str) -> str:
    if not email:
        return "user"
    try:
        response = get("/auth/role", headers={"X-User-Email": email})
        response.raise_for_status()
        data = response.json()
        return data.get("role", "user")
    except Exception:
        return "user"
