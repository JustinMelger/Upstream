"""Metadata extraction and public-only bounded transport regression tests."""

import asyncio
from unittest.mock import AsyncMock

import httpx
import pytest

from backend.core.errors import ServiceError
from backend.services import safe_page_fetch as fetch, url_preview_service as metadata


pytestmark = [pytest.mark.unit, pytest.mark.anyio]


@pytest.mark.parametrize(
    "url",
    [
        "file:///etc/passwd",
        "ftp://example.com",
        "http://localhost",
        "http://x.localhost",
        "http://user:pass@example.com",
        "http://example.com:8080",
        "https://example.com:80",
        "https://example.com/\nsecret",
        "http://[broken",
    ],
)
def test_invalid_urls(url):
    with pytest.raises(ServiceError):
        fetch.validate_url(url)


@pytest.mark.parametrize(
    "ip",
    ["127.0.0.1", "10.0.0.1", "169.254.169.254", "100.64.0.1", "::1", "fc00::1", "fe80::1", "::ffff:127.0.0.1", "224.0.0.1"],
)
async def test_private_addresses(ip):
    with pytest.raises(ServiceError):
        await fetch.resolve_addresses(ip)


async def test_mixed_dns(monkeypatch):
    monkeypatch.setattr(
        asyncio.get_running_loop(),
        "getaddrinfo",
        AsyncMock(return_value=[(0, 0, 0, "", ("8.8.8.8", 0)), (0, 0, 0, "", ("10.0.0.1", 0))]),
    )
    with pytest.raises(ServiceError):
        await fetch.resolve_addresses("example.com")


class Stream(httpx.AsyncByteStream):
    def __init__(self, chunks):
        self.chunks = chunks
        self.consumed = False
        self.closed = False

    async def __aiter__(self):
        self.consumed = True
        for chunk in self.chunks:
            yield chunk

    async def aclose(self):
        self.closed = True


def transport(monkeypatch, handler):
    requests = []

    class Transport:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def handle_async_request(self, request):
            requests.append(request)
            return handler(request, len(requests))

    monkeypatch.setattr(fetch.httpx, "AsyncHTTPTransport", lambda **kwargs: Transport())
    return requests


async def test_pinned_tls_redirect_and_no_redirect_body(monkeypatch):
    resolver = AsyncMock(side_effect=[["8.8.8.8"], ["1.1.1.1"]])
    monkeypatch.setattr(fetch, "resolve_addresses", resolver)
    redirect = Stream([b"do not consume"])
    body = Stream([b"<title>Hello</title>"])
    requests = transport(
        monkeypatch,
        lambda r, n: (
            httpx.Response(302, headers={"location": "https://next.example/final"}, stream=redirect)
            if n == 1
            else httpx.Response(200, headers={"content-type": "text/html"}, stream=body)
        ),
    )
    url, result = await fetch.fetch_html("https://example.com/start")
    assert url == "https://next.example/final" and "Hello" in result
    assert [r.url.host for r in requests] == ["8.8.8.8", "1.1.1.1"]
    assert [r.headers["host"] for r in requests] == ["example.com", "next.example"]
    assert requests[0].extensions["sni_hostname"] == "example.com"
    assert "cookie" not in requests[0].headers and "authorization" not in requests[0].headers
    assert resolver.await_count == 2
    assert redirect.closed and not redirect.consumed and body.closed


async def test_block_private_redirect(monkeypatch):
    original = fetch.resolve_addresses

    async def resolve(host):
        return ["8.8.8.8"] if host == "example.com" else await original(host)

    monkeypatch.setattr(fetch, "resolve_addresses", resolve)
    requests = transport(
        monkeypatch, lambda r, n: httpx.Response(302, headers={"location": "http://127.0.0.1/secret"}, stream=Stream([]))
    )
    with pytest.raises(ServiceError):
        await fetch.fetch_html("https://example.com")
    assert len(requests) == 1


@pytest.mark.parametrize(
    "headers,chunks",
    [
        ({"content-type": "application/json"}, [b"{}"]),
        ({"content-type": "text/html", "content-encoding": "gzip"}, [b"compressed"]),
        ({"content-type": "text/html", "content-length": "1000001"}, []),
        ({"content-type": "text/html"}, [b"x" * 600000, b"x" * 500000]),
    ],
)
async def test_reject_unusable_and_oversized(monkeypatch, headers, chunks):
    monkeypatch.setattr(fetch, "resolve_addresses", AsyncMock(return_value=["8.8.8.8"]))
    stream = Stream(chunks)
    transport(monkeypatch, lambda r, n: httpx.Response(200, headers=headers, stream=stream))
    with pytest.raises(ServiceError):
        await fetch.fetch_html("https://example.com")
    assert stream.closed


async def test_redirect_limit(monkeypatch):
    monkeypatch.setattr(fetch, "resolve_addresses", AsyncMock(return_value=["8.8.8.8"]))
    requests = transport(monkeypatch, lambda r, n: httpx.Response(302, headers={"location": "/again"}, stream=Stream([])))
    with pytest.raises(ServiceError):
        await fetch.fetch_html("https://example.com")
    assert len(requests) == 4


async def test_metadata_precedence_limits_and_cache(monkeypatch):
    html = (
        '<title>Fallback</title><meta name="twitter:title" content="Twitter"><meta property="og:title" content="A &amp; &lt;b&gt; B"><meta name="description" content="Standard"><meta property="og:description" content="'
        + "z" * 2100
        + '"><meta property="og:site_name" content="Docs"><meta property="og:image" content="https://internal/image">'
    )
    call = AsyncMock(return_value=("https://example.com/final", html))
    monkeypatch.setattr(metadata, "fetch_html", call)
    service = metadata.UrlPreviewService()
    result = await service.resolve_metadata(source_url="https://example.com")
    assert result["title"] == "A & B" and len(result["description"]) == 2000
    assert result["suggested_provider"] == "Docs" and result["normalized_url"].endswith("/final")
    assert result["preview_image_url"] == result["suggested_category"] == result["suggested_learning_item_type"] == ""
    assert result["suggested_tags"] == []
    assert await service.resolve_metadata(source_url="https://example.com") == result
    assert call.await_count == 1
    for i in range(257):
        await service.resolve_metadata(source_url=f"https://example.com/{i}")
    assert len(service._metadata_cache) == 256


@pytest.mark.parametrize(
    "html,title,description",
    [
        ("<title>  Simple\n title </title>", "Simple title", ""),
        ('<meta name="twitter:title" content="Twitter"><meta name="twitter:description" content="Text">', "Twitter", "Text"),
        ("<html></html>", "", ""),
    ],
)
async def test_fallback_and_missing_metadata(monkeypatch, html, title, description):
    monkeypatch.setattr(metadata, "fetch_html", AsyncMock(return_value=("https://example.com", html)))
    result = await metadata.UrlPreviewService().resolve_metadata(source_url="https://example.com")
    assert result["title"] == title and result["description"] == description
    assert result["suggested_provider"] == ""


async def test_timeout_is_generic_and_not_cached(monkeypatch):
    monkeypatch.setattr(metadata, "fetch_html", AsyncMock(side_effect=TimeoutError))
    service = metadata.UrlPreviewService()
    with pytest.raises(ServiceError, match="metadata_fetch_failed"):
        await service.resolve_metadata(source_url="https://example.com/secret?q=private")
    assert not service._metadata_cache


async def test_deadline_covers_dns(monkeypatch):
    original_timeout = asyncio.timeout
    monkeypatch.setattr(metadata.asyncio, "timeout", lambda seconds: original_timeout(0.01))

    async def stalled_dns(host):
        await asyncio.sleep(60)
        return ["8.8.8.8"]

    monkeypatch.setattr(fetch, "resolve_addresses", stalled_dns)
    with pytest.raises(ServiceError, match="metadata_fetch_failed"):
        await metadata.UrlPreviewService().resolve_metadata(source_url="https://example.com")


async def test_concurrent_fetches_are_bounded(monkeypatch):
    active = 0
    maximum = 0
    entered = asyncio.Event()
    release = asyncio.Event()

    async def delayed(url, **kwargs):
        nonlocal active, maximum
        active += 1
        maximum = max(maximum, active)
        if active == 4:
            entered.set()
        await release.wait()
        active -= 1
        return url, "<title>Result</title>"

    monkeypatch.setattr(metadata, "fetch_html", delayed)
    service = metadata.UrlPreviewService()
    tasks = [asyncio.create_task(service.resolve_metadata(source_url=f"https://example.com/{i}")) for i in range(8)]
    await asyncio.wait_for(entered.wait(), 1)
    assert maximum == 4
    release.set()
    await asyncio.gather(*tasks)
    assert maximum == 4


async def test_ipv6_pinning_preserves_host_header(monkeypatch):
    requests = transport(
        monkeypatch,
        lambda r, n: httpx.Response(200, headers={"content-type": "text/html"}, stream=Stream([b"<title>IPv6</title>"])),
    )
    await fetch.fetch_html("https://[2606:4700:4700::1111]/")
    assert requests[0].url.host == "2606:4700:4700::1111"
    assert requests[0].headers["host"] == "[2606:4700:4700::1111]"
