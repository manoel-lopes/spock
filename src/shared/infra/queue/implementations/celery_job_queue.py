from typing import Any

from src.shared.infra.queue.ports.job_queue import JobQueue
from src.shared.workers.celery_app import celery_app


class CeleryJobQueue(JobQueue):
    async def add(self, name: str, data: dict[str, Any]) -> str:
        result = celery_app.send_task(
            "src.shared.workers.tasks.report_analysis.process_report_analysis",
            args=[data],
            queue="report-analysis",
        )
        return result.id

    async def get_status(self, job_id: str) -> str | None:
        result = celery_app.AsyncResult(job_id)
        if result.state == "PENDING":
            return "pending"
        if result.state == "STARTED":
            return "processing"
        if result.state == "SUCCESS":
            return "completed"
        if result.state == "FAILURE":
            return "failed"
        return result.state.lower()
