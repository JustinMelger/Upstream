from __future__ import annotations


"""HTTP client wrapper for the NiceGUI frontend.

This module centralizes all HTTP concerns:

- Base URL handling.
- `X-Session-Token` header injection for authenticated requests.
- Mapping backend "service error" envelopes into `ApiError`.

The backend uses a standard error envelope like:
`{"status": "error", "message": "...", "timestamp": "..."}`.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, UTC
from typing import Any, Callable

import httpx


@dataclass(frozen=True, slots=True)
class ApiError(Exception):
    """Represents an API error returned by the backend (or mapped from HTTP failures).

    Attributes:
        status_code: HTTP status code.
        message: Human-readable error message.
        timestamp: Optional backend-provided timestamp (ISO-8601 string).
    """

    status_code: int
    message: str
    timestamp: str | None = None

    def __str__(self) -> str:
        return f"{self.status_code}: {self.message}"


class ApiClient:
    """HTTP client wrapper for the FastAPI backend."""

    def __init__(
        self,
        *,
        base_url: str,
        token_provider: Callable[[], str | None],
        timeout_s: float = 10.0,
    ) -> None:
        """Create an API client.

        Args:
            base_url: Backend base URL, e.g. `http://localhost:8000`.
            token_provider: Callable that returns the current `X-Session-Token` value.
            timeout_s: Per-request timeout in seconds.
        """
        self._base_url = base_url.rstrip("/")
        self._token_provider = token_provider
        self._timeout = timeout_s
        # Keep a persistent client for connection pooling.
        # This noticeably improves UI responsiveness vs. creating a new client per request.
        self._client = httpx.AsyncClient(base_url=self._base_url, timeout=self._timeout)

    async def aclose(self) -> None:
        """Close the underlying HTTP client.

        Note:
            This should be hooked into NiceGUI shutdown to avoid unclosed
            connection warnings in development.
        """
        await self._client.aclose()

    def _headers(self, *, token_override: str | None = None) -> dict[str, str]:
        """Build request headers for the current session."""
        token = token_override if token_override is not None else self._token_provider()
        if not token:
            return {}
        return {"X-Session-Token": token}

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        token_override: str | None = None,
    ) -> Any:
        """Send an HTTP request to the backend.

        Args:
            method: HTTP method (e.g. `"GET"`).
            path: Absolute backend path (e.g. `"/courses"`).
            params: Optional query parameters.
            json: Optional JSON payload for write operations.
            token_override: Optional token to use instead of the current store token.

        Returns:
            Parsed JSON body when the response is JSON; otherwise `None`.

        Raises:
            ApiError: On backend error envelopes or non-2xx responses.
        """
        try:
            resp = await self._client.request(
                method,
                path,
                headers=self._headers(token_override=token_override),
                params=params,
                json=json,
            )
        except httpx.RequestError as exc:
            # Keep network failures user-friendly; callers can display `str(ApiError)`.
            raise ApiError(status_code=503, message=f"backend_unreachable: {exc.__class__.__name__}") from exc

        content_type = resp.headers.get("content-type", "")
        body: Any = None
        if "application/json" in content_type:
            body = resp.json()

        # Standard error envelope from backend: {"status":"error","message":...,"timestamp":...}
        if isinstance(body, dict) and body.get("status") == "error" and "message" in body:
            raise ApiError(status_code=resp.status_code, message=str(body.get("message")), timestamp=str(body.get("timestamp")))

        if resp.status_code >= 400:
            # Fallback for non-envelope errors.
            message = None
            if isinstance(body, dict) and "detail" in body:
                message = str(body.get("detail"))
            raise ApiError(status_code=resp.status_code, message=message or resp.reason_phrase)

        self._emit_product_action_telemetry(
            method=str(method or "").upper(),
            path=str(path or ""),
        )

        return body

    def _emit_product_action_telemetry(self, *, method: str, path: str) -> None:
        """Emit low-noise telemetry for key share/track actions."""
        if method != "POST":
            return
        event_name = ""
        if path == "/tracking":
            event_name = "track_action"
        elif path == "/courses":
            event_name = "share_course"
        elif path == "/paths":
            event_name = "share_path"
        elif path == "/articles":
            event_name = "share_article"
        if not event_name:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        loop.create_task(self._post_telemetry_event(event_name=event_name, context={"path": path}))

    async def _post_telemetry_event(self, *, event_name: str, context: dict[str, Any]) -> None:
        """Best-effort telemetry POST, intentionally detached from request flow."""
        try:
            resp = await self._client.request(
                "POST",
                "/telemetry/events",
                headers=self._headers(),
                json={
                    "event_name": str(event_name),
                    "context": dict(context or {}),
                    "happened_at": datetime.now(UTC).isoformat(),
                },
            )
            if resp.status_code >= 400:
                return
        except httpx.RequestError:
            return

    async def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        """Send a GET request."""
        return await self.request("GET", path, params=params)

    async def post(self, path: str, payload: dict[str, Any], *, token_override: str | None = None) -> Any:
        """Send a POST request."""
        return await self.request("POST", path, json=payload, token_override=token_override)

    async def put(self, path: str, payload: dict[str, Any]) -> Any:
        """Send a PUT request."""
        return await self.request("PUT", path, json=payload)

    async def delete(self, path: str) -> Any:
        """Send a DELETE request."""
        return await self.request("DELETE", path)
