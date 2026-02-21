"""Course media parsing helpers (YouTube-safe embed support)."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse


_YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")


def extract_youtube_video_id(url: str | None) -> str | None:
    """Return a validated YouTube video id from a URL, or None."""
    raw = str(url or "").strip()
    if not raw:
        return None
    parsed = urlparse(raw)
    host = str(parsed.netloc or "").lower()
    path_parts = [p for p in str(parsed.path or "").split("/") if p]

    candidate = ""
    if host in {"youtu.be", "www.youtu.be"}:
        candidate = path_parts[0] if path_parts else ""
    elif host in {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com"}:
        if parsed.path == "/watch":
            candidate = str(parse_qs(parsed.query).get("v", [""])[0] or "")
        elif path_parts and path_parts[0] in {"embed", "shorts", "live"}:
            candidate = path_parts[1] if len(path_parts) > 1 else ""

    if not _YOUTUBE_ID_RE.fullmatch(candidate):
        return None
    return candidate


def youtube_embed_url(video_id: str) -> str:
    """Build a safe embed URL for a known-valid YouTube video id."""
    return f"https://www.youtube.com/embed/{video_id}?rel=0"


def youtube_thumbnail_url(video_id: str) -> str:
    """Build a stable YouTube thumbnail URL for a known-valid video id."""
    return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"


def youtube_thumbnail_fallback_url(video_id: str) -> str:
    """Build fallback YouTube thumbnail URL for host-level failures."""
    return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"


def render_youtube_embed(embed_url: str, *, title: str = "Course video preview") -> str:
    """Return YouTube iframe HTML for a trusted embed URL."""
    safe_url = str(embed_url or "").strip()
    safe_title = str(title or "Course video preview")
    if not safe_url:
        return ""
    return (
        f'<iframe src="{safe_url}" '
        f'title="{safe_title}" '
        'allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
        "allowfullscreen "
        'referrerpolicy="strict-origin-when-cross-origin"></iframe>'
    )
