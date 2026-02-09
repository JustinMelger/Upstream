from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.api import auth, courses, paths, tracking
from backend.api.schemas import HealthResponse
from backend.core.config import settings
from backend.core.errors import (
    AuthServiceError,
    CoursesServiceError,
    format_service_error,
    PathsServiceError,
    TrackingServiceError,
    UserPathsServiceError,
)


app = FastAPI(title=settings.api_title, version=settings.api_version)

app.include_router(courses.router)
app.include_router(paths.router)
app.include_router(tracking.router)
app.include_router(auth.router)


@app.exception_handler(AuthServiceError)
async def auth_service_exception_handler(request: Request, exc: AuthServiceError):
    return JSONResponse(status_code=exc.status_code, content=format_service_error(exc))


@app.exception_handler(CoursesServiceError)
async def courses_service_exception_handler(request: Request, exc: CoursesServiceError):
    return JSONResponse(status_code=exc.status_code, content=format_service_error(exc))


@app.exception_handler(PathsServiceError)
async def paths_service_exception_handler(request: Request, exc: PathsServiceError):
    return JSONResponse(status_code=exc.status_code, content=format_service_error(exc))


@app.exception_handler(UserPathsServiceError)
async def user_paths_service_exception_handler(request: Request, exc: UserPathsServiceError):
    return JSONResponse(status_code=exc.status_code, content=format_service_error(exc))


@app.exception_handler(TrackingServiceError)
async def tracking_service_exception_handler(request: Request, exc: TrackingServiceError):
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
