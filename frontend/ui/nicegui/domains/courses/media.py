"""Course media parsing helpers (YouTube-safe embed support)."""

from __future__ import annotations

import re
from urllib.parse import parse_qs, quote, urlparse


_YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_DIMENSION_HINT_RE = re.compile(r"(?<!\d)(\d{1,4})[xX](\d{1,4})(?!\d)")
_SIZE_PARAM_NAMES = {"w", "width", "h", "height", "size", "sz"}
_LOW_QUALITY_KEYWORDS = ("favicon", "avatar", "sprite")


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


def website_favicon_url(source_url: str | None) -> str:
    """Build a generic favicon URL for non-video websites."""
    raw = str(source_url or "").strip()
    if not raw:
        return ""
    parsed = urlparse(raw)
    if str(parsed.scheme or "").lower() not in {"http", "https"}:
        return ""
    host = str(parsed.hostname or "").strip().lower()
    if not host:
        return ""
    return f"https://www.google.com/s2/favicons?domain={quote(host)}&sz=256"


def is_low_quality_preview_image_url(image_url: str | None) -> bool:
    """Return whether a preview image URL looks too small/icon-like for card media."""
    raw = str(image_url or "").strip()
    if not raw:
        return False

    parsed = urlparse(raw)
    haystack = " ".join(part for part in (str(parsed.path or "").lower(), str(parsed.query or "").lower()) if part)
    if any(keyword in haystack for keyword in _LOW_QUALITY_KEYWORDS):
        return True

    host = str(parsed.hostname or "").strip().lower()
    if host in {"www.google.com", "google.com"} and str(parsed.path or "").startswith("/s2/favicons"):
        return True

    for match in _DIMENSION_HINT_RE.finditer(haystack):
        try:
            width = int(match.group(1))
            height = int(match.group(2))
        except (TypeError, ValueError):
            continue
        if width <= 96 and height <= 96:
            return True

    query = parse_qs(parsed.query)
    size_hints: list[int] = []
    for key in _SIZE_PARAM_NAMES:
        for value in list(query.get(key, [])):
            try:
                size_hints.append(int(str(value).strip()))
            except (TypeError, ValueError):
                continue
    return bool(size_hints) and max(size_hints) <= 96


def preferred_preview_image_url(image_url: str | None) -> str:
    """Normalize preview image URLs so obvious low-quality assets fall back to local placeholders."""
    raw = str(image_url or "").strip()
    if not raw:
        return ""
    return "" if is_low_quality_preview_image_url(raw) else raw


def preferred_card_image_url(*, image_url: str | None, source_url: str | None, allow_favicon_fallback: bool = True) -> str:
    """Return the preferred card image URL, optionally falling back to a generic website favicon."""
    normalized_preview = preferred_preview_image_url(image_url)
    if normalized_preview:
        return normalized_preview
    if not allow_favicon_fallback:
        return ""
    return website_favicon_url(source_url)


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
