FROM python:3.13 AS compile-image

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

RUN uv venv /.venv --python 3.13
ENV VIRTUAL_ENV=/.venv
ENV PATH="/.venv/bin:$PATH"

COPY pyproject.toml uv.lock ./
RUN uv sync --active --no-install-project

FROM python:3.13-slim-bookworm AS build-image

COPY --from=compile-image /.venv /.venv
ENV VIRTUAL_ENV=/.venv
ENV PATH="/.venv/bin:$PATH"

WORKDIR /app
COPY . .

ENV PYTHONUNBUFFERED=1
ENV PORT=8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
