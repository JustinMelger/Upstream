"""Smart fallback examples when URL metadata extraction returns little/no data."""

from __future__ import annotations

from urllib.parse import urlparse


def _host_label(url: str) -> str:
    host = str(urlparse(str(url or "").strip()).hostname or "").strip().lower()
    if host.startswith("www."):
        host = host[4:]
    if not host:
        return "Source"
    root = host.split(".")[0].replace("-", " ").replace("_", " ").strip()
    label = " ".join(part for part in root.split() if part)
    return label.title() if label else "Source"


def build_course_metadata_fallback(*, url: str) -> dict[str, str]:
    """Build fallback examples for course share fields."""
    source = _host_label(url)
    topic = str(source or "General").strip()
    topic_lower = topic.lower()
    return {
        "title": f"{source} {topic} Learning Path",
        "description": f"Practical {topic_lower} resource curated from {source}.",
        "provider": source,
        "category": topic,
        "learning_outcomes": f"Suggested topics: {topic_lower}, fundamentals, practical skills",
    }


def build_article_metadata_fallback(*, url: str) -> dict[str, str]:
    """Build fallback examples for article share fields."""
    source = _host_label(url)
    topic = str(source or "General").strip()
    topic_lower = topic.lower()
    return {
        "title": f"{source}: key takeaways",
        "tags": f"{topic_lower}, reading, reference",
    }
