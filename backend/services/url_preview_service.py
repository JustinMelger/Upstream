from __future__ import annotations

import asyncio
from collections import OrderedDict
import html
from html.parser import HTMLParser
import re
import time

import httpx

from backend.core.errors import ServiceError
from backend.services.safe_page_fetch import fetch_html, validate_url


class UrlPreviewService:
    """Suggest page-authored metadata using bounded, validated fetching."""

    def __init__(self, *, ttl_seconds: float = 900.0, max_response_bytes: int = 1_000_000) -> None:
        """Initialize the successful-result cache and concurrent fetch limit."""
        self._ttl_seconds = float(ttl_seconds)
        self._max_response_bytes = int(max_response_bytes)
        self._metadata_cache: OrderedDict[str, tuple[float, dict[str, object]]] = OrderedDict()
        self._metadata_slots = asyncio.Semaphore(4)

    async def resolve_metadata(self, *, source_url: str) -> dict[str, object]:
        """Return bounded page-authored suggestions without image fetching."""
        url = str(validate_url(source_url))
        cached = self._metadata_cache.get(url)
        if cached and cached[0] > time.monotonic():
            self._metadata_cache.move_to_end(url)
            return dict(cached[1])
        try:
            async with asyncio.timeout(10):
                async with self._metadata_slots:
                    normalized, body = await fetch_html(url, max_bytes=self._max_response_bytes)
        except (TimeoutError, httpx.HTTPError, OSError, ValueError) as exc:
            raise ServiceError(detail="metadata_fetch_failed", status_code=502) from exc
        parser = PageMetadataParser()
        parser.feed(body)
        meta = parser.meta
        payload = self._empty_metadata(url=url)
        payload.update(
            {
                "normalized_url": normalized,
                "title": clean_text(meta.get("og:title") or meta.get("twitter:title") or parser.title, 300),
                "description": clean_text(
                    meta.get("og:description") or meta.get("description") or meta.get("twitter:description") or "", 2000
                ),
                "site_name": clean_text(meta.get("og:site_name", ""), 300),
                "suggested_provider": clean_text(meta.get("og:site_name", ""), 300),
            }
        )
        self._metadata_cache[url] = (time.monotonic() + self._ttl_seconds, dict(payload))
        self._metadata_cache.move_to_end(url)
        while len(self._metadata_cache) > 256:
            self._metadata_cache.popitem(last=False)
        return payload

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


class PageMetadataParser(HTMLParser):
    """Read page metadata without executing markup or fetching subresources."""

    def __init__(self) -> None:
        """Initialize extracted values."""
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.title = ""
        self.in_title = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """Collect nonblank metadata and enter title text."""
        values = dict(attrs)
        if tag == "meta":
            key = (values.get("property") or values.get("name") or "").lower()
            value = values.get("content") or ""
            if value.strip() and key not in self.meta:
                self.meta[key] = value
        elif tag == "title":
            self.in_title = True

    def handle_endtag(self, tag: str) -> None:
        """Stop title collection at its closing tag."""
        if tag == "title":
            self.in_title = False

    def handle_data(self, data: str) -> None:
        """Collect text only while inside the title."""
        if self.in_title:
            self.title += data


def clean_text(value: str, limit: int) -> str:
    """Normalize page-authored text into a bounded, non-markup suggestion."""
    value = re.sub(r"<[^>]*>", " ", html.unescape(value))
    return " ".join(value.split())[:limit]
