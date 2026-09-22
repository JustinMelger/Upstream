from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.api import articles, auth, browser_auth, courses, paths, tracking, url_preview, videos, workspace
from backend.api.schemas import HealthResponse
from backend.core.browser_security import BrowserSessionMiddleware
from backend.core.config import settings
from backend.core.errors import (
    format_service_error,
    ServiceError,
)
from backend.core.observability import configure_observability


app = FastAPI(title=settings.api_title, version=settings.api_version, root_path=settings.api_root_path)
configure_observability(app)
app.add_middleware(BrowserSessionMiddleware)
app.include_router(browser_auth.router)
app.include_router(workspace.router)

app.include_router(courses.router)
app.include_router(paths.router)
app.include_router(tracking.router)
app.include_router(auth.router)
app.include_router(articles.router)
app.include_router(videos.router)
app.include_router(url_preview.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    """Return a standard envelope for non-domain HTTP errors."""
    return JSONResponse(status_code=exc.status_code, content=format_service_error(exc))


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(_request: Request, _exc: RequestValidationError) -> JSONResponse:
    """Return a standard envelope for request validation errors."""
    return JSONResponse(
        status_code=422,
        content=format_service_error(HTTPException(status_code=422, detail="validation_error")),
    )


@app.exception_handler(ServiceError)
async def service_error_exception_handler(_request: Request, exc: ServiceError) -> JSONResponse:
    """Return a standard envelope for service-domain errors."""
    return JSONResponse(status_code=exc.status_code, content=format_service_error(exc))


@app.get("/health", tags=["health"], response_model=HealthResponse)
def health() -> dict[str, str]:
    """Health check endpoint.

    Returns:
        dict: Simple status payload.
    """
    return {"status": "ok"}
