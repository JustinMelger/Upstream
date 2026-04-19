from __future__ import annotations

import asyncio

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


@pytest.mark.unit
async def test_url_preview_service_resolves_vimeo_thumbnail_via_oembed(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    class _Response:
        status_code = 200
        headers = {"content-type": "application/json"}
        content = b'{"thumbnail_url":"https://i.vimeocdn.com/video/1234567890-640.jpg"}'

        @staticmethod
        def json() -> dict[str, str]:
            return {"thumbnail_url": "https://i.vimeocdn.com/video/1234567890-640.jpg"}

    class _Client:
        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
            return None

        async def get(self, url: str):  # noqa: ANN001
            calls.append(url)
            return _Response()

    from backend.services import url_preview_service as module

    monkeypatch.setattr(module.httpx, "AsyncClient", lambda **kwargs: _Client())
    service = UrlPreviewService()
    image = await service.resolve_image_url(source_url="https://vimeo.com/76979871")
    assert image == "https://i.vimeocdn.com/video/1234567890-640.jpg"
    assert any("vimeo.com/api/oembed.json" in call for call in calls)


@pytest.mark.unit
async def test_url_preview_service_rejects_private_hosts_without_network() -> None:
    service = UrlPreviewService()
    image = await service.resolve_image_url(source_url="http://127.0.0.1/internal")
    assert image == ""


@pytest.mark.unit
async def test_url_preview_service_resolves_metadata_suggestions(monkeypatch: pytest.MonkeyPatch) -> None:
    html = """
    <html><head>
      <title>Testing FastAPI apps</title>
      <meta property="og:site_name" content="FastAPI Docs">
      <meta name="description" content="Test FastAPI applications with pytest and httpx.">
      <meta property="og:image" content="/img/social.png">
      <meta name="keywords" content="fastapi, python, testing">
    </head></html>
    """

    class _Response:
        status_code = 200
        headers = {"content-type": "text/html; charset=utf-8"}
        text = html
        content = html.encode("utf-8")
        url = "https://fastapi.tiangolo.com/tutorial/testing/"

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
    payload = await service.resolve_metadata(source_url="https://fastapi.tiangolo.com/tutorial/testing/")
    assert payload["title"] == "Testing FastAPI apps"
    assert payload["suggested_learning_item_type"] == "article"
    assert payload["suggested_provider"] == "FastAPI Docs"
    assert payload["suggested_category"] in {"Backend", "Programming"}
    assert payload["preview_image_url"] == "https://fastapi.tiangolo.com/img/social.png"
    assert any(str(tag).lower() == "fastapi" for tag in list(payload["suggested_tags"] or []))


@pytest.mark.unit
async def test_url_preview_service_suggests_video_and_course_types_without_extra_rules() -> None:
    service = UrlPreviewService()
    youtube = await service.resolve_metadata(source_url="https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    udemy = await service.resolve_metadata(source_url="https://www.udemy.com/course/fastapi-zero-to-prod/")
    assert youtube["suggested_learning_item_type"] == "video"
    assert udemy["suggested_learning_item_type"] == "course"


@pytest.mark.unit
async def test_url_preview_service_blocks_redirect_to_private_host(monkeypatch: pytest.MonkeyPatch) -> None:
    class _RedirectResponse:
        status_code = 302
        headers = {"location": "http://127.0.0.1/internal"}
        is_redirect = True

    class _Client:
        async def __aenter__(self) -> "_Client":
            return self

        async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
            return None

        async def get(self, url: str):  # noqa: ANN001
            assert url == "https://example.com/course"
            return _RedirectResponse()

    from backend.services import url_preview_service as module

    monkeypatch.setattr(module.httpx, "AsyncClient", lambda **kwargs: _Client())
    service = UrlPreviewService()
    monkeypatch.setattr(service, "_host_resolves_publicly", lambda host: asyncio.sleep(0, result=True if host == "example.com" else False))

    payload = await service.resolve_metadata(source_url="https://example.com/course")
    assert payload["title"] == ""
    assert payload["preview_image_url"] == ""
    assert payload["normalized_url"] == "https://example.com/course"


@pytest.mark.unit
async def test_url_preview_service_rejects_hostnames_that_resolve_to_private_ips(monkeypatch: pytest.MonkeyPatch) -> None:
    service = UrlPreviewService()
    monkeypatch.setattr(
        service,
        "_host_resolves_publicly",
        lambda host: asyncio.sleep(0, result=False if host == "internal.example" else True),
    )

    payload = await service.resolve_metadata(source_url="https://internal.example/course")
    assert payload["title"] == ""
    assert payload["preview_image_url"] == ""
    assert payload["source_url"] == "https://internal.example/course"
