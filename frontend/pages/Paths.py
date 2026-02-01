import sys
from pathlib import Path
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ui.style import apply_global_style
from services.api import get

st.set_page_config(page_title="Learning Paths", page_icon="🧭", layout="wide")
apply_global_style()

st.title("🧭 Learning Paths")
st.caption("Curated paths to guide learning journeys.")

try:
    response = get("/paths")
    response.raise_for_status()
    paths = response.json()
except Exception:
    paths = []
    st.error("Could not reach API.")

if not paths:
    st.info("No learning paths yet. Admins can add these later.")
else:
    for path in paths:
        st.subheader(path.get("name", "(untitled path)"))
        if path.get("description"):
            st.write(path["description"])
        st.divider()
