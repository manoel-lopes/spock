#!/bin/sh
set -e

# Run Alembic migrations before starting services
echo "Running database migrations..."
python -m alembic upgrade head

# Start Celery worker in background with solo pool (low memory footprint)
echo "Starting Celery worker..."
celery -A src.shared.workers.celery_app worker \
  --loglevel=info \
  --pool=solo \
  --concurrency=1 &

# Start uvicorn in foreground
echo "Starting uvicorn..."
uvicorn src.main:app --host 0.0.0.0 --port "${PORT:-8000}"
