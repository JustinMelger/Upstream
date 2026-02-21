from __future__ import annotations

import pytest

from backend.services.url_preview_service import UrlPreviewService


pytestmark = pytest.mark.anyio


@pytest.mark.unit
async def test_url_preview_service_resolves_youtube_thumbnail_without_network() -> None:
    service = UrlPreviewService()
    image = await service.resolve_image_url(source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    assert image == "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg"


@pytest.mark.unit
async def test_url_preview_service_parses_open_graph_image(monkeypatch: pytest.MonkeyPatch) -> None:
    html = """
    <html><head>
      <meta property="og:image" content="/assets/cover.png">
    </head></html>
    """

    class _Response:
        status_code = 200
        headers = {"content-type": "text/html; charset=utf-8"}
        text = html

    class _Client:
        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
            return None

        async def get(self, url: str):  # noqa: ANN001
            return _Response()

    from backend.services import url_preview_service as module

    monkeypatch.setattr(module.httpx, "AsyncClient", lambda **kwargs: _Client())
    service = UrlPreviewService()
    image = await service.resolve_image_url(source_url="https://example.com/course")
    assert image == "https://example.com/assets/cover.png"


@pytest.mark.unit
async def test_url_preview_service_caches_result(monkeypatch: pytest.MonkeyPatch) -> None:
    calls = 0

    class _Response:
        status_code = 200
        headers = {"content-type": "text/html"}
        text = '<meta property="og:image" content="https://cdn.example.com/cover.png">'

    class _Client:
        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
            return None

        async def get(self, url: str):  # noqa: ANN001
            nonlocal calls
            calls += 1
            return _Response()

    from backend.services import url_preview_service as module

    monkeypatch.setattr(module.httpx, "AsyncClient", lambda **kwargs: _Client())
    service = UrlPreviewService(ttl_seconds=60.0)
    first = await service.resolve_image_url(source_url="https://example.com/course")
    second = await service.resolve_image_url(source_url="https://example.com/course")
    assert first == "https://cdn.example.com/cover.png"
    assert second == first
    assert calls == 1
