FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src/ ./src/
COPY alembic/ ./alembic/
COPY alembic.ini ./

RUN pip install --no-cache-dir .

EXPOSE 8000
COPY entrypoint.sh ./
CMD ["./entrypoint.sh"]
