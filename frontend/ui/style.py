import streamlit as st


def apply_global_style() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
  font-family: "Space Grotesk", system-ui, sans-serif;
}
</style>
""",
        unsafe_allow_html=True,
    )
