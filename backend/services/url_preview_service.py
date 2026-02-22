from __future__ import annotations

import asyncio
import html
import ipaddress
import re
import time
from urllib.parse import parse_qs, urlencode, urljoin, urlparse

import httpx


_YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
_VIMEO_ID_RE = re.compile(r"^[0-9]{6,12}$")
_META_RE = re.compile(
    r"<meta[^>]+(?:property|name)\s*=\s*['\"](?P<key>og:image|twitter:image)['\"][^>]*content\s*=\s*['\"](?P<val>[^'\"]+)['\"][^>]*>",
    re.IGNORECASE,
)
_META_RE_INVERTED = re.compile(
    r"<meta[^>]+content\s*=\s*['\"](?P<val>[^'\"]+)['\"][^>]*(?:property|name)\s*=\s*['\"](?P<key>og:image|twitter:image)['\"][^>]*>",
    re.IGNORECASE,
)
_META_ANY_RE = re.compile(
    r"<meta[^>]+(?:property|name)\s*=\s*['\"](?P<key>[^'\"]+)['\"][^>]*content\s*=\s*['\"](?P<val>[^'\"]*)['\"][^>]*>",
    re.IGNORECASE,
)
_META_ANY_RE_INVERTED = re.compile(
    r"<meta[^>]+content\s*=\s*['\"](?P<val>[^'\"]*)['\"][^>]*(?:property|name)\s*=\s*['\"](?P<key>[^'\"]+)['\"][^>]*>",
    re.IGNORECASE,
)
_TITLE_RE = re.compile(r"<title[^>]*>(?P<title>.*?)</title>", re.IGNORECASE | re.DOTALL)
_LOCAL_HOSTS = {"localhost", "localhost.localdomain", "127.0.0.1", "::1"}
_OEMBED_PROVIDERS: dict[str, str] = {
    "vimeo.com": "https://vimeo.com/api/oembed.json",
    "www.vimeo.com": "https://vimeo.com/api/oembed.json",
    "player.vimeo.com": "https://vimeo.com/api/oembed.json",
}


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


def _extract_vimeo_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    host = str(parsed.netloc or "").lower()
    if host not in {"vimeo.com", "www.vimeo.com", "player.vimeo.com"}:
        return None
    path_parts = [p for p in str(parsed.path or "").split("/") if p]
    candidate = ""
    if host == "player.vimeo.com":
        if len(path_parts) >= 2 and path_parts[0] == "video":
            candidate = path_parts[1]
    else:
        candidate = path_parts[0] if path_parts else ""
    if not _VIMEO_ID_RE.fullmatch(candidate):
        return None
    return candidate


def _is_safe_public_host(host: str) -> bool:
    value = str(host or "").strip().lower()
    if not value:
        return False
    if value in _LOCAL_HOSTS:
        return False
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return True
    if ip.is_private or ip.is_loopback or ip.is_link_local:
        return False
    if ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        return False
    return True


class UrlPreviewService:
    """Resolve static preview image URLs for course links with short TTL caching."""

    def __init__(
        self,
        *,
        ttl_seconds: float = 900.0,
        timeout_seconds: float = 4.0,
        max_response_bytes: int = 1_000_000,
    ) -> None:
        self._ttl_seconds = float(ttl_seconds)
        self._timeout_seconds = float(timeout_seconds)
        self._max_response_bytes = int(max_response_bytes)
        self._cache: dict[str, tuple[float, str]] = {}
        self._metadata_cache: dict[str, tuple[float, dict[str, object]]] = {}
        self._lock = asyncio.Lock()

    async def resolve_image_url(self, *, source_url: str) -> str:
        url = str(source_url or "").strip()
        if not url:
            return ""
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return ""
        if not _is_safe_public_host(parsed.hostname or ""):
            return ""

        now = time.monotonic()
        cached = self._cache.get(url)
        if cached and cached[0] > now:
            return cached[1]

        image_url = self._from_youtube(url)
        if not image_url:
            image_url = await self._from_oembed(url)
        if not image_url:
            image_url = await self._from_open_graph(url)

        async with self._lock:
            self._cache[url] = (time.monotonic() + self._ttl_seconds, image_url)
        return image_url

    async def resolve_metadata(self, *, source_url: str) -> dict[str, object]:
        """Resolve URL metadata used for form autofill suggestions."""
        url = str(source_url or "").strip()
        if not url:
            return self._empty_metadata(url="")
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return self._empty_metadata(url=url)
        if not _is_safe_public_host(parsed.hostname or ""):
            return self._empty_metadata(url=url)

        now = time.monotonic()
        cached = self._metadata_cache.get(url)
        if cached and cached[0] > now:
            return dict(cached[1])

        body = ""
        response = await self._safe_get(url)
        if response is not None and int(response.status_code) < 400:
            content_type = str(response.headers.get("content-type") or "").lower()
            if "text/html" in content_type:
                body = str(response.text or "")[:250_000]

        meta = self._extract_html_metadata(body)
        site_name = str(meta.get("og:site_name") or "").strip()
        title = str(meta.get("og:title") or meta.get("twitter:title") or "").strip()
        if not title and body:
            title_match = _TITLE_RE.search(body)
            if title_match:
                title = html.unescape(str(title_match.group("title") or "").strip())
        description = str(meta.get("og:description") or meta.get("description") or "").strip()
        image_url = await self.resolve_image_url(source_url=url)
        normalized_url = str(response.url) if response is not None else url
        provider = self._suggest_provider(site_name=site_name, source_url=normalized_url)
        tags = self._suggest_tags(meta=meta, title=title, description=description)
        category = self._suggest_category(title=title, description=description, tags=tags)
        payload = {
            "source_url": url,
            "normalized_url": normalized_url,
            "title": title,
            "description": description,
            "site_name": site_name,
            "preview_image_url": image_url,
            "suggested_provider": provider,
            "suggested_category": category,
            "suggested_tags": tags,
        }
        async with self._lock:
            self._metadata_cache[url] = (time.monotonic() + self._ttl_seconds, dict(payload))
        return payload

    @staticmethod
    def _from_youtube(url: str) -> str:
        video_id = _extract_youtube_video_id(url)
        if not video_id:
            return ""
        return f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

    async def _from_oembed(self, url: str) -> str:
        parsed = urlparse(url)
        provider_endpoint = _OEMBED_PROVIDERS.get(str(parsed.netloc or "").lower(), "")
        if not provider_endpoint:
            return ""
        params = urlencode({"url": url})
        endpoint_url = f"{provider_endpoint}?{params}"
        response = await self._safe_get(endpoint_url)
        if response is None:
            return ""
        content_type = str(response.headers.get("content-type") or "").lower()
        if "application/json" not in content_type and "text/json" not in content_type:
            return ""
        try:
            payload = dict(response.json() or {})
        except ValueError:
            return ""
        candidate = str(payload.get("thumbnail_url") or "").strip()
        if not candidate:
            # Vimeo sometimes returns thumbnail_url_with_play_button in some variants.
            candidate = str(payload.get("thumbnail_url_with_play_button") or "").strip()
        if not candidate:
            return ""
        return self._safe_image_candidate(base_url=url, candidate=candidate)

    async def _from_open_graph(self, url: str) -> str:
        response = await self._safe_get(url)
        if response is None:
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
        return self._safe_image_candidate(base_url=url, candidate=candidate)

    @staticmethod
    def _extract_html_metadata(body: str) -> dict[str, str]:
        out: dict[str, str] = {}
        if not body:
            return out
        for regex in (_META_ANY_RE, _META_ANY_RE_INVERTED):
            for match in regex.finditer(body):
                key = str(match.group("key") or "").strip().lower()
                value = html.unescape(str(match.group("val") or "").strip())
                if key and value and key not in out:
                    out[key] = value
        return out

    @staticmethod
    def _suggest_provider(*, site_name: str, source_url: str) -> str:
        candidate = str(site_name or "").strip()
        if candidate:
            return candidate
        host = str(urlparse(source_url).hostname or "").strip().lower()
        if host.startswith("www."):
            host = host[4:]
        core = host.split(".")[0] if host else ""
        if not core:
            return ""
        return core.replace("-", " ").replace("_", " ").title()

    @staticmethod
    def _suggest_tags(*, meta: dict[str, str], title: str, description: str) -> list[str]:
        tags: list[str] = []
        seen: set[str] = set()
        keywords = str(meta.get("keywords") or "")
        for part in keywords.split(","):
            value = str(part or "").strip()
            key = value.lower()
            if not value or key in seen:
                continue
            seen.add(key)
            tags.append(value)
            if len(tags) >= 6:
                return tags

        corpus = f"{title} {description}".lower()
        heuristics = [
            ("fastapi", "FastAPI"),
            ("sqlalchemy", "SQLAlchemy"),
            ("python", "Python"),
            ("database", "Database"),
            ("api", "API"),
            ("testing", "Testing"),
            ("docker", "Docker"),
            ("kubernetes", "Kubernetes"),
            ("aws", "AWS"),
            ("machine learning", "Machine Learning"),
            ("ai", "AI"),
        ]
        for needle, label in heuristics:
            if needle not in corpus:
                continue
            key = label.lower()
            if key in seen:
                continue
            seen.add(key)
            tags.append(label)
            if len(tags) >= 6:
                break
        return tags

    @staticmethod
    def _suggest_category(*, title: str, description: str, tags: list[str]) -> str:
        corpus = f"{title} {description} {' '.join(tags)}".lower()
        rules = [
            (("fastapi", "api", "backend", "http", "flask", "django"), "Backend"),
            (("sql", "database", "postgres", "mysql", "orm"), "Database"),
            (("docker", "kubernetes", "devops", "cloud", "mlops"), "DevOps"),
            (("machine learning", "neural", "ai"), "AI/ML"),
            (("react", "frontend", "javascript", "typescript", "css", "html"), "Frontend"),
            (("python", "java", "rust", "go"), "Programming"),
        ]
        for needles, category in rules:
            if any(n in corpus for n in needles):
                return category
        return ""

    @staticmethod
    def _empty_metadata(*, url: str) -> dict[str, object]:
        return {
            "source_url": str(url or ""),
            "normalized_url": str(url or ""),
            "title": "",
            "description": "",
            "site_name": "",
            "preview_image_url": "",
            "suggested_provider": "",
            "suggested_category": "",
            "suggested_tags": [],
        }

    def _safe_image_candidate(self, *, base_url: str, candidate: str) -> str:
        if not candidate:
            return ""
        absolute = urljoin(base_url, candidate)
        parsed = urlparse(absolute)
        if parsed.scheme not in {"http", "https"}:
            return ""
        if not _is_safe_public_host(parsed.hostname or ""):
            return ""
        return absolute

    async def _safe_get(self, url: str) -> httpx.Response | None:
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return None
        if not _is_safe_public_host(parsed.hostname or ""):
            return None
        try:
            async with httpx.AsyncClient(
                follow_redirects=True,
                timeout=self._timeout_seconds,
                headers={"User-Agent": "LearningHubBot/1.0 (+https://learning-hub.local)"},
            ) as client:
                response = await client.get(url)
        except httpx.HTTPError:
            return None
        content_length = str(response.headers.get("content-length") or "").strip()
        if content_length:
            try:
                if int(content_length) > self._max_response_bytes:
                    return None
            except ValueError:
                return None
        body_bytes = getattr(response, "content", b"") or b""
        if len(body_bytes) > self._max_response_bytes:
            return None
        return response
