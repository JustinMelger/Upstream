FROM python:3.13-slim-bookworm AS compile-image

WORKDIR /app

RUN pip install --no-cache-dir uv

RUN uv venv /.venv --python 3.13
ENV VIRTUAL_ENV=/.venv
ENV PATH="/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN uv sync --active --no-install-project --frozen --no-dev

FROM python:3.13-slim-bookworm AS runtime

COPY --from=compile-image /.venv /.venv
ENV VIRTUAL_ENV=/.venv
ENV PATH="/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000

RUN groupadd --gid 10001 app && \
    useradd --uid 10001 --gid app --create-home app
WORKDIR /app
COPY --chown=app:app backend ./backend
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app alembic.ini ./alembic.ini

USER 10001:10001
EXPOSE 8000
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
