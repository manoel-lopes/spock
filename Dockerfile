FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

RUN pip install --no-cache-dir .

# Combined: uvicorn + celery worker in a single container
FROM base AS web
EXPOSE 8000
COPY entrypoint.sh ./
CMD ["./entrypoint.sh"]

# Standalone worker (for paid tier later)
FROM base AS worker
CMD ["celery", "-A", "src.shared.workers.celery_app", "worker", "--loglevel=info", "--concurrency=2"]
