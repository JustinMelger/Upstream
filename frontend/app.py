import os
import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Learning Hub", page_icon="📚", layout="wide")

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")


@st.cache_data
def load_courses():
    try:
        response = requests.get(f"{API_BASE_URL}/courses", timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception:
        return (
            pd.DataFrame(columns=["title", "provider", "category", "level", "duration_hours", "url"]),
            f"Could not reach API at {API_BASE_URL}.",
        )

    df = pd.DataFrame(data)
    for col in ["title", "provider", "category", "level", "duration_hours", "url"]:
        if col not in df.columns:
            df[col] = ""

    for col in ["title", "provider", "category", "level", "url"]:
        df[col] = df[col].fillna("").astype(str)

    df["duration_hours"] = pd.to_numeric(df["duration_hours"], errors="coerce")
    return df, None


@st.cache_data
def load_tracking(colleague_id: str):
    if not colleague_id:
        return {}
    try:
        response = requests.get(
            f"{API_BASE_URL}/tracking", params={"colleague_id": colleague_id}, timeout=10
        )
        response.raise_for_status()
        data = response.json()
    except Exception:
        return {}

    status_map = {}
    for item in data:
        try:
            course_id = int(item.get("course_id", 0))
        except ValueError:
            continue
        status_map[course_id] = item.get("status", "")
    return status_map


def card_start():
    st.markdown('<div class="card">', unsafe_allow_html=True)


def card_end():
    st.markdown("</div>", unsafe_allow_html=True)


# Page styling + card styling (works without st.container(border=...))
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:wght@600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');

:root {
  --ink: #0f172a;
  --muted: #5b6475;
  --accent: #1f7a8c;
  --accent-2: #ef6351;
  --card: #ffffff;
  --stroke: rgba(15, 23, 42, 0.12);
  --glow: rgba(31, 122, 140, 0.15);
  --bg: #f7f6f2;
  --sidebar: #eef3f6;
}

.stApp {
  background: radial-gradient(1200px 600px at 10% -10%, var(--glow), transparent 60%),
              radial-gradient(900px 500px at 90% 0%, rgba(239, 99, 81, 0.12), transparent 55%),
              var(--bg);
  color: var(--ink);
  font-family: "Space Grotesk", system-ui, sans-serif;
}

section[data-testid="stSidebar"] {
  background: var(--sidebar);
  border-right: 1px solid var(--stroke);
}

section[data-testid="stSidebar"] .stMarkdown,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] p {
  color: var(--ink);
}

h1, h2, h3, .hero-title {
  font-family: "Fraunces", Georgia, serif;
  letter-spacing: -0.02em;
}

.hero {
  padding: 1.5rem 0 1rem 0;
}

.hero-title {
  font-size: 2.4rem;
  margin: 0 0 0.35rem 0;
}

.hero-sub {
  color: var(--muted);
  font-size: 1.05rem;
  margin: 0 0 1rem 0;
}

.stat-row {
  display: flex;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.stat {
  background: rgba(31, 122, 140, 0.08);
  border: 1px solid var(--stroke);
  border-radius: 999px;
  padding: 0.35rem 0.85rem;
  font-size: 0.95rem;
  color: var(--ink);
}

.card {
  padding: 1rem;
  border: 1px solid var(--stroke);
  border-radius: 16px;
  margin-bottom: 0.75rem;
  background: var(--card);
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
  animation: fadeUp 420ms ease both;
}

.card-title {
  margin: 0 0 0.25rem 0;
  font-size: 1.2rem;
}

.card-meta {
  color: var(--muted);
  font-size: 0.95rem;
  margin-bottom: 0.5rem;
}

.pill {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.2rem 0.6rem;
  border-radius: 999px;
  border: 1px solid var(--stroke);
  background: rgba(31, 122, 140, 0.08);
  color: var(--ink);
  font-size: 0.85rem;
  margin-right: 0.35rem;
}

.pill.alt {
  background: rgba(239, 99, 81, 0.1);
}

.smallmeta {
  color: var(--muted);
  font-size: 0.9rem;
}

.link-muted {
  color: var(--accent);
  font-weight: 600;
}

.count {
  color: var(--muted);
  font-weight: 500;
  margin: 0.25rem 0 0.5rem 0;
}

.stLinkButton > button {
  background: var(--accent);
  color: white;
  border: none;
  padding: 0.5rem 0.9rem;
  border-radius: 10px;
  font-weight: 600;
}

.stLinkButton > button:hover {
  background: #176070;
}

@media (prefers-color-scheme: dark) {
  :root {
    --ink: #e5e7eb;
    --muted: #a6adbb;
    --accent: #62b6cb;
    --accent-2: #ff9f8d;
    --card: #111827;
    --stroke: rgba(148, 163, 184, 0.22);
    --glow: rgba(98, 182, 203, 0.15);
    --bg: #0b0f19;
    --sidebar: #121826;
  }

  .card {
    box-shadow: 0 10px 24px rgba(2, 6, 23, 0.5);
  }

  .stLinkButton > button:hover {
    background: #4aa0b6;
  }
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
""",
    unsafe_allow_html=True,
)

df, load_error = load_courses()

if load_error:
    st.error(load_error)
    try:
        health = requests.get(f"{API_BASE_URL}/health", timeout=5)
        st.caption(f"API health: {health.status_code} {health.text}")
    except Exception:
        st.caption("API health: not reachable")

# Hero header
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

# Sidebar filters
st.sidebar.header("Filters")
colleague_id = st.sidebar.text_input("Your name or email", "")
search = st.sidebar.text_input("Search", "")
category = st.sidebar.multiselect("Category", sorted([c for c in df["category"].unique() if c]))
provider = st.sidebar.multiselect("Provider", sorted([p for p in df["provider"].unique() if p]))
level = st.sidebar.multiselect("Level", sorted([l for l in df["level"].unique() if l]))

filtered = df.copy()

if search.strip():
    s = search.strip().lower()
    filtered = filtered[
        filtered.apply(
            lambda r: s in (r["title"] + " " + r["category"] + " " + r["provider"]).lower(),
            axis=1,
        )
    ]

if category:
    filtered = filtered[filtered["category"].isin(category)]
if provider:
    filtered = filtered[filtered["provider"].isin(provider)]
if level:
    filtered = filtered[filtered["level"].isin(level)]

st.markdown(
    f"<div class='count'>Showing <strong>{len(filtered)}</strong> of <strong>{len(df)}</strong> courses</div>",
    unsafe_allow_html=True,
)

# Tracking map
tracking_map = load_tracking(colleague_id.strip())

# Render items
for _, row in filtered.iterrows():
    card_start()
    col1, col2 = st.columns([5, 1])

    with col1:
        title = row["title"] or "(untitled)"
        pill_bits = []
        if row["provider"]:
            pill_bits.append(f"<span class='pill'>🏢 {row['provider']}</span>")
        if row["category"]:
            pill_bits.append(f"<span class='pill alt'>🏷️ {row['category']}</span>")
        if row["level"]:
            pill_bits.append(f"<span class='pill'>🎯 {row['level']}</span>")

        st.markdown(f"<h3 class='card-title'>{title}</h3>", unsafe_allow_html=True)
        if pill_bits:
            st.markdown("".join(pill_bits), unsafe_allow_html=True)

        meta_bits = []
        if pd.notna(row["duration_hours"]):
            meta_bits.append(f"⏱ {row['duration_hours']} hours")
        if meta_bits:
            st.markdown(f"<div class='card-meta'>{' • '.join(meta_bits)}</div>", unsafe_allow_html=True)

        if row["url"]:
            st.markdown(f"<a class='link-muted' href='{row['url']}'>{row['url']}</a>", unsafe_allow_html=True)
        else:
            st.warning("Missing URL")

    with col2:
        if row["url"]:
            # Works on modern Streamlit; if very old, user can click the URL text anyway
            try:
                st.link_button("Open", row["url"])
            except Exception:
                st.markdown(f"[Open]({row['url']})")

        course_id = int(row.get("id", 0) or 0)
        if course_id:
            current_status = tracking_map.get(course_id, "")
            status = st.selectbox(
                "Status",
                ["", "interested", "in_progress", "completed"],
                index=["", "interested", "in_progress", "completed"].index(current_status or ""),
                key=f"status_{course_id}",
            )
            if st.button("Save status", key=f"save_{course_id}"):
                if not colleague_id.strip():
                    st.warning("Enter your name/email in the sidebar first.")
                else:
                    try:
                        response = requests.post(
                            f"{API_BASE_URL}/tracking",
                            json={
                                "colleague_id": colleague_id.strip(),
                                "course_id": course_id,
                                "status": status,
                            },
                            timeout=10,
                        )
                        response.raise_for_status()
                        st.success("Status saved.")
                        st.cache_data.clear()
                    except Exception:
                        st.error("Could not save status.")

    card_end()

st.divider()

# Optional: add course form (persists to CSV)
with st.expander("➕ Add a course"):
    st.info("Read-only mode. Course edits will be added later via the admin service.")
