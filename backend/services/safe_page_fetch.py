"""Bounded HTML fetching with validated, pinned public destinations."""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from urllib.parse import urljoin

import httpx

from backend.core.errors import ServiceError


def public_address(value: str) -> bool:
    """Reject special-use addresses, including IPv4 mapped into IPv6."""
    address = ipaddress.ip_address(value)
    if isinstance(address, ipaddress.IPv6Address) and address.ipv4_mapped:
        address = address.ipv4_mapped
    return address.is_global and not address.is_multicast and not address.is_reserved


def validate_url(value: str) -> httpx.URL:
    """Accept only credential-free standard HTTP destinations."""
    try:
        if any(ord(char) < 32 for char in value) or "\\" in value:
            raise ValueError
        url = httpx.URL(value.strip())
        if (
            url.scheme not in {"http", "https"}
            or not url.host
            or "%" in url.host
            or url.userinfo
            or url.port not in {None, 80 if url.scheme == "http" else 443}
            or url.host.rstrip(".").lower() == "localhost"
            or url.host.rstrip(".").lower().endswith(".localhost")
        ):
            raise ValueError
        return url.copy_with(fragment=None)
    except (ValueError, httpx.InvalidURL) as exc:
        raise ServiceError(detail="metadata_invalid_url", status_code=422) from exc


async def resolve_addresses(host: str) -> list[str]:
    """Resolve once and reject mixed public/private DNS answers."""
    try:
        try:
            ipaddress.ip_address(host)
            addresses = [host]
        except ValueError:
            records = await asyncio.get_running_loop().getaddrinfo(host, None, type=socket.SOCK_STREAM)
            addresses = sorted({str(record[4][0]) for record in records})
        if not addresses or not all(public_address(address) for address in addresses):
            raise ServiceError(detail="metadata_blocked_url", status_code=422)
        return addresses
    except OSError as exc:
        raise ServiceError(detail="metadata_fetch_failed", status_code=502) from exc


async def fetch_html(source: str, *, max_bytes: int = 1_000_000) -> tuple[str, str]:
    """Fetch at most four pinned destinations without cookies or automatic redirects.

    The caller supplies an overall deadline covering DNS and body consumption.
    Identity encoding avoids unbounded decompression allocations from hostile pages.
    """
    current = source
    for hop in range(4):
        url = validate_url(current)
        addresses = await resolve_addresses(url.host)
        pinned = url.copy_with(host=addresses[0])
        request = httpx.Request(
            "GET",
            pinned,
            headers={
                "Host": url.netloc.decode("ascii"),
                "User-Agent": "LearningHubBot/1.0",
                "Accept": "text/html, application/xhtml+xml",
                "Accept-Encoding": "identity",
            },
            extensions={
                "sni_hostname": url.host,
                "timeout": {name: 4.0 for name in ("connect", "read", "write", "pool")},
            },
        )
        # Direct transport avoids cookie state, environment proxies, and HTTPX's
        # client-level URL logging. TLS verification still uses the original SNI.
        async with httpx.AsyncHTTPTransport(retries=0, trust_env=False) as transport:
            response = await transport.handle_async_request(request)
            try:
                if response.status_code in {301, 302, 303, 307, 308}:
                    location = response.headers.get("location")
                    if not location or hop == 3:
                        raise ServiceError(detail="metadata_fetch_failed", status_code=502)
                    current = urljoin(str(url), location)
                    continue
                media = response.headers.get("content-type", "").split(";", 1)[0].strip().lower()
                if (
                    response.status_code >= 400
                    or media not in {"text/html", "application/xhtml+xml"}
                    or response.headers.get("content-encoding", "identity").lower() != "identity"
                ):
                    raise ServiceError(detail="metadata_fetch_failed", status_code=502)
                length = response.headers.get("content-length")
                if length and (not length.isdecimal() or int(length) > max_bytes):
                    raise ServiceError(detail="metadata_fetch_failed", status_code=502)
                body = bytearray()
                async for chunk in response.aiter_raw():
                    if len(body) + len(chunk) > max_bytes:
                        raise ServiceError(detail="metadata_fetch_failed", status_code=502)
                    body.extend(chunk)
                decoded = httpx.Response(200, headers=response.headers, content=bytes(body)).text
                return str(url), decoded
            finally:
                await response.aclose()
    raise ServiceError(detail="metadata_fetch_failed", status_code=502)
