from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.api import auth, courses, paths, tracking
from backend.api.schemas import HealthResponse
from backend.core.config import settings
from backend.core.errors import (
    format_service_error,
    ServiceError,
)


app = FastAPI(title=settings.api_title, version=settings.api_version)

app.include_router(courses.router)
app.include_router(paths.router)
app.include_router(tracking.router)
app.include_router(auth.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Return a standard envelope for non-domain HTTP errors."""
    return JSONResponse(status_code=exc.status_code, content=format_service_error(exc))


@app.exception_handler(RequestValidationError)
async def request_validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return a standard envelope for request validation errors."""
    return JSONResponse(
        status_code=422,
        content=format_service_error(HTTPException(status_code=422, detail="validation_error")),
    )


@app.exception_handler(ServiceError)
async def service_error_exception_handler(request: Request, exc: ServiceError):
    """Return a standard envelope for service-domain errors."""
    return JSONResponse(status_code=exc.status_code, content=format_service_error(exc))


@app.get("/health", tags=["health"], response_model=HealthResponse)
def health():
    """Health check endpoint.

    Returns:
        dict: Simple status payload.
    """
    return {"status": "ok"}


def on_startup():
    """Deprecated: schema work is handled by Alembic."""
    return None
