from __future__ import annotations

import asyncio
import html
import ipaddress
import re
import socket
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
_VIDEO_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
    "www.youtu.be",
    "vimeo.com",
    "www.vimeo.com",
    "player.vimeo.com",
}
_COURSE_HOSTS = {
    "udemy.com",
    "www.udemy.com",
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


def _is_safe_public_ip(value: str) -> bool:
    """Return whether an IP literal is public and routable."""
    try:
        ip = ipaddress.ip_address(str(value or "").strip())
    except ValueError:
        return False
    if ip.is_private or ip.is_loopback or ip.is_link_local:
        return False
    if ip.is_multicast or ip.is_reserved or ip.is_unspecified:
        return False
    return True


def _is_safe_public_host(host: str) -> bool:
    value = str(host or "").strip().lower()
    if not value:
        return False
    if value in _LOCAL_HOSTS:
        return False
    try:
        ipaddress.ip_address(value)
    except ValueError:
        return True
    return _is_safe_public_ip(value)


class UrlPreviewService:
    """Resolve static preview image URLs for course links with short TTL caching."""

    def __init__(
        self,
        *,
        ttl_seconds: float = 900.0,
        timeout_seconds: float = 4.0,
        max_response_bytes: int = 1_000_000,
    ) -> None:
        """Initialize URL preview resolver caches and limits.

        Args:
            ttl_seconds: Cache TTL for resolved previews/metadata.
            timeout_seconds: HTTP request timeout.
            max_response_bytes: Maximum response body size to process.

        """
        self._ttl_seconds = float(ttl_seconds)
        self._timeout_seconds = float(timeout_seconds)
        self._max_response_bytes = int(max_response_bytes)
        self._cache: dict[str, tuple[float, str]] = {}
        self._metadata_cache: dict[str, tuple[float, dict[str, object]]] = {}
        self._lock = asyncio.Lock()

    async def _validate_resolvable_url(self, *, source_url: str) -> tuple[str, bool]:
        url = str(source_url or "").strip()
        if not url:
            return "", False
        parsed = urlparse(url)
        if parsed.scheme not in {"http", "https"}:
            return url, False
        if not _is_safe_public_host(parsed.hostname or ""):
            return url, False
        if not await self._host_resolves_publicly(parsed.hostname or ""):
            return url, False
        return url, True

    def _normalize_resolvable_host(self, host: str) -> str:
        """Return a normalized hostname when it is worth resolving."""
        hostname = str(host or "").strip()
        if not hostname:
            return ""
        if not _is_safe_public_host(hostname):
            return ""
        return hostname

    def _public_ip_literal_status(self, host: str) -> bool | None:
        """Return public-IP status for IP literals, or None for hostnames."""
        try:
            ipaddress.ip_address(host)
        except ValueError:
            return None
        return _is_safe_public_ip(host)

    async def _resolve_public_addresses(self, host: str) -> set[str]:
        """Return the resolved public address candidates for one hostname."""
        try:
            infos = await asyncio.get_running_loop().getaddrinfo(
                host,
                None,
                type=socket.SOCK_STREAM,
                proto=socket.IPPROTO_TCP,
            )
        except OSError:
            return set()

        addresses: set[str] = set()
        for _family, _socktype, _proto, _canonname, sockaddr in infos:
            candidate = str(sockaddr[0] or "").strip()
            if candidate:
                addresses.add(candidate)
        return addresses

    async def _host_resolves_publicly(self, host: str) -> bool:
        """Return whether a hostname resolves only to safe public IPs."""
        hostname = self._normalize_resolvable_host(host)
        if not hostname:
            return False
        literal_status = self._public_ip_literal_status(hostname)
        if literal_status is not None:
            return literal_status

        addresses = await self._resolve_public_addresses(hostname)
        if not addresses:
            return False
        return all(_is_safe_public_ip(address) for address in addresses)

    async def resolve_image_url(self, *, source_url: str) -> str:
        """Resolve a preview image URL for a source link.

        Args:
            source_url: Source URL to inspect.

        Returns:
            Preview image URL or empty string when unavailable.

        """
        url, is_valid = await self._validate_resolvable_url(source_url=source_url)
        if not is_valid:
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
        url, is_valid = await self._validate_resolvable_url(source_url=source_url)
        if not is_valid:
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
        learning_item_type = self._suggest_learning_item_type(source_url=normalized_url, provider=provider)
        tags = self._suggest_tags(meta=meta, title=title, description=description)
        category = self._suggest_category(title=title, description=description, tags=tags)
        payload: dict[str, object] = {
            "source_url": url,
            "normalized_url": normalized_url,
            "suggested_learning_item_type": learning_item_type,
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
    def _suggest_learning_item_type(*, source_url: str, provider: str) -> str:
        host = str(urlparse(source_url).hostname or "").strip().lower()
        provider_value = str(provider or "").strip().lower()
        if host in _VIDEO_HOSTS or "youtube" in provider_value or "vimeo" in provider_value:
            return "video"
        if host in _COURSE_HOSTS or "udemy" in provider_value:
            return "course"
        return "article"

    @staticmethod
    def _append_keyword_tags(*, tags: list[str], seen: set[str], keywords: str) -> bool:
        for part in str(keywords or "").split(","):
            if not UrlPreviewService._append_tag_if_new(tags=tags, seen=seen, value=str(part or "")):
                continue
            if len(tags) >= 6:
                return True
        return False

    @staticmethod
    def _append_heuristic_tags(*, tags: list[str], seen: set[str], corpus: str) -> None:
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
            if not UrlPreviewService._append_tag_if_new(tags=tags, seen=seen, value=label):
                continue
            if len(tags) >= 6:
                break

    @staticmethod
    def _suggest_tags(*, meta: dict[str, str], title: str, description: str) -> list[str]:
        tags: list[str] = []
        seen: set[str] = set()
        corpus = f"{title} {description}".lower()
        if UrlPreviewService._append_keyword_tags(tags=tags, seen=seen, keywords=str(meta.get("keywords") or "")):
            return tags
        UrlPreviewService._append_heuristic_tags(tags=tags, seen=seen, corpus=corpus)
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
            "suggested_learning_item_type": "",
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

    @staticmethod
    def _append_tag_if_new(*, tags: list[str], seen: set[str], value: str) -> bool:
        clean = str(value or "").strip()
        key = clean.lower()
        if not clean or key in seen:
            return False
        seen.add(key)
        tags.append(clean)
        return True

    def _response_within_limit(self, response: httpx.Response) -> bool:
        content_length = str(response.headers.get("content-length") or "").strip()
        if content_length:
            try:
                if int(content_length) > self._max_response_bytes:
                    return False
            except ValueError:
                return False
        body_bytes = getattr(response, "content", b"") or b""
        return len(body_bytes) <= self._max_response_bytes

    async def _safe_get(self, url: str) -> httpx.Response | None:
        current_url = str(url or "").strip()
        response: httpx.Response | None = None
        try:
            async with httpx.AsyncClient(
                follow_redirects=False,
                timeout=self._timeout_seconds,
                trust_env=False,
                headers={"User-Agent": "LearningHubBot/1.0 (+https://learning-hub.local)"},
            ) as client:
                for _ in range(4):
                    parsed = urlparse(current_url)
                    is_safe_request = (
                        parsed.scheme in {"http", "https"}
                        and _is_safe_public_host(parsed.hostname or "")
                        and await self._host_resolves_publicly(parsed.hostname or "")
                    )
                    if not is_safe_request:
                        break

                    response = await client.get(current_url)
                    if bool(getattr(response, "is_redirect", False)):
                        location = str(response.headers.get("location") or "").strip()
                        if not location:
                            response = None
                            break
                        current_url = urljoin(current_url, location)
                        response = None
                        continue

                    if self._response_within_limit(response):
                        return response
                    response = None
                    break
        except httpx.HTTPError:
            response = None
        return response
