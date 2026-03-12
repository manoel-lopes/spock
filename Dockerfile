FROM python:3.12-slim AS base

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

RUN pip install --no-cache-dir .

# Web
FROM base AS web
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Worker
FROM base AS worker
CMD ["celery", "-A", "src.shared.workers.celery_app", "worker", "--loglevel=info", "--concurrency=2"]
