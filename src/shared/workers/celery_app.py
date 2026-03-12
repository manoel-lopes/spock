from celery import Celery

from src.shared.infra.env.env_service import env_service

celery_app = Celery(
    "spock",
    broker=env_service.redis_url,
    backend=env_service.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_concurrency=1,
    worker_pool="solo",
    worker_prefetch_multiplier=1,
    task_time_limit=300,
    task_soft_time_limit=280,
    task_default_queue="report-analysis",
    task_acks_late=True,
    worker_max_tasks_per_child=50,
)

import src.shared.workers.tasks.report_analysis  # noqa: F401, E402
