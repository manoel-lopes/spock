#!/bin/sh
set -e

echo "Running database migrations..."
python -m alembic upgrade head

echo "Starting uvicorn..."
exec uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"
