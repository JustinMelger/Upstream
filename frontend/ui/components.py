import pandas as pd
import streamlit as st


def card_start() -> None:
    st.markdown('<div class="card">', unsafe_allow_html=True)


def card_end() -> None:
    st.markdown("</div>", unsafe_allow_html=True)


def hero_header(df: pd.DataFrame) -> None:
    st.markdown(
        f"""
<div class="hero">
  <div class="hero-title">Learning Hub</div>
  <div class="hero-sub">Curated courses and resources for colleagues — pick a path and jump in.</div>
  <div class="stat-row">
    <div class="stat">📚 {len(df)} courses</div>
    <div class="stat">🏷️ {df['category'].replace('', pd.NA).nunique()} categories</div>
    <div class="stat">🏢 {df['provider'].replace('', pd.NA).nunique()} providers</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def course_pills(row: pd.Series) -> str:
    pills = []
    if row.get("provider"):
        pills.append(f"<span class='pill'>🏢 {row['provider']}</span>")
    if row.get("category"):
        pills.append(f"<span class='pill alt'>🏷️ {row['category']}</span>")
    if row.get("level"):
        pills.append(f"<span class='pill'>🎯 {row['level']}</span>")
    return "".join(pills)


def course_meta(row: pd.Series) -> str:
    meta = []
    if pd.notna(row.get("duration_hours")):
        meta.append(f"⏱ {row['duration_hours']} hours")
    return " • ".join(meta)
