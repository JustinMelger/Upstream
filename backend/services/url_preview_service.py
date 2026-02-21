from __future__ import annotations

import asyncio
import html
import re
import time
from urllib.parse import parse_qs, urljoin, urlparse

import httpx


_YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_META_RE = re.compile(
    r"<meta[^>]+(?:property|name)\s*=\s*['\"](?P<key>og:image|twitter:image)['\"][^>]*content\s*=\s*['\"](?P<val>[^'\"]+)['\"][^>]*>",
    re.IGNORECASE,
)
_META_RE_INVERTED = re.compile(
    r"<meta[^>]+content\s*=\s*['\"](?P<val>[^'\"]+)['\"][^>]*(?:property|name)\s*=\s*['\"](?P<key>og:image|twitter:image)['\"][^>]*>",
    re.IGNORECASE,
)


def _extract_youtube_video_id(url: str) -> str | None:
    parsed = urlparse(url)
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


class UrlPreviewService:
    """Resolve static preview image URLs for course links with short TTL caching."""

    def __init__(self, *, ttl_seconds: float = 900.0, timeout_seconds: float = 4.0) -> None:
        self._ttl_seconds = float(ttl_seconds)
        self._timeout_seconds = float(timeout_seconds)
        self._cache: dict[str, tuple[float, str]] = {}
        self._lock = asyncio.Lock()

    async def resolve_image_url(self, *, source_url: str) -> str:
        url = str(source_url or "").strip()
        if not url:
            return ""
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return ""

        now = time.monotonic()
        cached = self._cache.get(url)
        if cached and cached[0] > now:
            return cached[1]

        image_url = self._from_youtube(url)
        if not image_url:
            image_url = await self._from_open_graph(url)

        async with self._lock:
            self._cache[url] = (time.monotonic() + self._ttl_seconds, image_url)
        return image_url

    @staticmethod
    def _from_youtube(url: str) -> str:
        video_id = _extract_youtube_video_id(url)
        if not video_id:
            return ""
        return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

    async def _from_open_graph(self, url: str) -> str:
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=self._timeout_seconds,
                headers={"User-Agent": "LearningHubBot/1.0 (+https://learning-hub.local)"},
            ) as client:
                response = await client.get(url)
        except Exception:
            return ""

        if int(response.status_code) >= 400:
            return ""
        content_type = str(response.headers.get("content-type") or "").lower()
        if "text/html" not in content_type:
            return ""

        body = str(response.text or "")[:250_000]
        match = _META_RE.search(body) or _META_RE_INVERTED.search(body)
        if not match:
            return ""
        candidate = html.unescape(str(match.group("val") or "").strip())
        if not candidate:
            return ""
        absolute = urljoin(url, candidate)
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"}:
            return ""
        return absolute
