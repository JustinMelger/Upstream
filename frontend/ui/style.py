import streamlit as st


def apply_global_style() -> None:
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
