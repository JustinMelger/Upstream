import streamlit as st


def apply_global_style() -> None:
    st.markdown(
        """
<style>
/* Hide Streamlit deploy button */
[data-testid="stDeployButton"] {
  display: none !important;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  background: rgba(31, 122, 140, 0.08);
  font-size: 0.8rem;
  margin-right: 0.35rem;
}

.pill.alt {
  background: rgba(239, 99, 81, 0.1);
}
</style>
""",
        unsafe_allow_html=True,
    )
