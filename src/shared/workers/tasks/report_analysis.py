import hashlib
import logging
import time
from datetime import datetime
from typing import Any

from src.shared.events.analyzer_registry import get_analyzer, get_content_validator
from src.shared.events.event_bus import DomainEvent, EventBus
from src.shared.events import events
from src.shared.infra.env.env_service import env_service
from src.shared.infra.persistence.models import (
    FundModel,
    ProcessingJobModel,
    ProcessingLogModel,
    ReportAnalysisModel,
    ReportContentModel,
    ReportModel,
)
from src.shared.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# Module-level event bus — set by main.py at startup
_event_bus: EventBus | None = None


def set_event_bus(bus: EventBus) -> None:
    global _event_bus
    _event_bus = bus


def _publish(event_name: str, payload: dict[str, Any]) -> None:
    if _event_bus:
        _event_bus.publish(DomainEvent(name=event_name, payload=payload))


# Reuse a single engine across tasks instead of creating one per invocation
_engine = None
_session_factory = None


def _get_sync_session():
    global _engine, _session_factory
    if _engine is None:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session, sessionmaker

        _engine = create_engine(
            env_service.sync_database_url,
            pool_size=4,
            max_overflow=4,
            pool_pre_ping=True,
            pool_recycle=300,
        )
        _session_factory = sessionmaker(_engine, class_=Session)
    return _session_factory()


class PermanentFailure(Exception):
    """Errors that should not be retried (bad PDF, missing data)."""


@celery_app.task(
    name="src.shared.workers.tasks.report_analysis.process_report_analysis",
    bind=True,
    max_retries=3,
    default_retry_delay=15,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=120,
)
def process_report_analysis(self, data: dict[str, Any]) -> None:
    processing_job_id = data["processingJobId"]
    report_id = data["reportId"]
    pdf_url = data["pdfUrl"]
    fund_type = data.get("fundType", "equity")
    force_redownload = data.get("forceRedownload", False)

    session = _get_sync_session()

    try:
        # Update job status to processing
        job = session.get(ProcessingJobModel, processing_job_id)
        if job:
            job.status = "processing"
            job.started_at = datetime.utcnow()
            job.attempts = (self.request.retries or 0) + 1
            session.commit()

        _publish(events.REPORT_SUBMITTED, {
            "report_id": report_id,
            "fund_type": fund_type,
            "pdf_url": pdf_url,
        })

        # Download & Extract
        text, page_count = _download_and_extract(
            session, processing_job_id, report_id, pdf_url, fund_type, force_redownload
        )

        # Analyze using the registered analyzer for this fund_type
        _analyze_report(session, processing_job_id, report_id, text, fund_type)

        # Mark completed
        report = session.get(ReportModel, report_id)
        if report:
            report.status = "completed"
            report.error_message = None

        _log_stage(session, processing_job_id, "complete", "completed")

        if job:
            job = session.get(ProcessingJobModel, processing_job_id)
            if job:
                job.status = "completed"
                job.completed_at = datetime.utcnow()

        session.commit()

        # Score (fire-and-forget)
        _score_report(session, processing_job_id, report_id)

    except PermanentFailure as e:
        # Don't retry permanent failures
        _mark_failed(session, processing_job_id, report_id, str(e))
        session.close()

    except Exception as e:
        _mark_failed(session, processing_job_id, report_id, str(e))
        session.close()
        raise self.retry(exc=e) from e

    finally:
        session.close()


def _mark_failed(session, processing_job_id: str, report_id: str, error_message: str) -> None:
    try:
        _log_stage(session, processing_job_id, "error", "failed", metadata={"error": error_message})

        report = session.get(ReportModel, report_id)
        if report:
            report.status = "failed"
            report.error_message = error_message

        job = session.get(ProcessingJobModel, processing_job_id)
        if job:
            job.status = "failed"
            job.error_message = error_message

        session.commit()
    except Exception:
        session.rollback()


def _download_and_extract(
    session,
    job_id: str,
    report_id: str,
    pdf_url: str,
    fund_type: str,
    force_redownload: bool,
) -> tuple[str, int]:
    if not force_redownload:
        from sqlalchemy import select
        stmt = select(ReportContentModel).where(ReportContentModel.report_id == report_id)
        existing = session.execute(stmt).scalar_one_or_none()
        if existing:
            _log_stage(session, job_id, "download", "skipped")
            _log_stage(session, job_id, "extract", "skipped")
            return existing.raw_text, existing.page_count

    # Download
    download_start = time.monotonic()
    _log_stage(session, job_id, "download", "started")

    report = session.get(ReportModel, report_id)
    if report:
        report.status = "downloading"
        session.commit()

    pdf_buffer = _download_pdf_sync(pdf_url)

    pdf_hash = hashlib.sha256(pdf_buffer).hexdigest()
    if report:
        report.pdf_hash = pdf_hash
        session.commit()

    download_ms = int((time.monotonic() - download_start) * 1000)
    _log_stage(session, job_id, "download", "completed", duration_ms=download_ms)

    _publish(events.REPORT_DOWNLOADED, {
        "report_id": report_id,
        "pdf_hash": pdf_hash,
    })

    # Extract
    extract_start = time.monotonic()
    _log_stage(session, job_id, "extract", "started")

    if report:
        report.status = "extracting"
        session.commit()

    extracted = _extract_pdf_sync(pdf_buffer, fund_type)

    content = ReportContentModel(
        report_id=report_id,
        raw_text=extracted["text"],
        normalized_text=extracted["text"].lower(),
        page_count=extracted["page_count"],
        parser_version="1.0.0",
    )
    session.add(content)
    session.commit()

    extract_ms = int((time.monotonic() - extract_start) * 1000)
    _log_stage(session, job_id, "extract", "completed", duration_ms=extract_ms)

    _publish(events.REPORT_EXTRACTED, {
        "report_id": report_id,
        "text": extracted["text"][:500],
        "page_count": extracted["page_count"],
    })

    return extracted["text"], extracted["page_count"]


def _download_pdf_sync(url: str) -> bytes:
    """Download PDF synchronously with retries and validation."""
    import base64

    import httpx

    with httpx.Client(timeout=httpx.Timeout(60.0, connect=15.0)) as client:
        for attempt in range(3):
            try:
                response = client.get(url, follow_redirects=True)
                response.raise_for_status()
                break
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                if attempt == 2:
                    raise
                logger.warning("Download attempt %d failed for %s: %s", attempt + 1, url, e)
                time.sleep(2 * (attempt + 1))

    raw = response.content
    text = response.text

    # Handle base64-encoded PDF response
    cleaned = text.strip().strip('"')
    if cleaned.startswith("JVBER"):
        return base64.b64decode(cleaned)

    # Handle raw PDF
    if raw[:5] == b"%PDF-":
        return raw

    # Handle latin-1 encoded PDF text
    buf = text.encode("latin-1")
    if buf[:5] == b"%PDF-":
        return buf

    # Not a valid PDF
    preview = text[:200] if len(text) > 200 else text
    raise PermanentFailure(f"Invalid PDF response (starts with: {preview[:80]})")


def _extract_pdf_sync(pdf_buffer: bytes, fund_type: str) -> dict[str, Any]:
    """Extract text from PDF synchronously."""
    import fitz

    try:
        doc = fitz.open(stream=pdf_buffer, filetype="pdf")
    except Exception as e:
        raise PermanentFailure(f"Invalid PDF structure: {e}") from e

    try:
        text = "\n".join(page.get_text() for page in doc)
        page_count = len(doc)
    finally:
        doc.close()

    if not text.strip():
        raise PermanentFailure("PDF has no extractable text")

    # Use the registered content validator for this fund type
    validator = get_content_validator(fund_type)
    validator.validate(text, page_count)

    return {"text": text, "page_count": page_count}


def _analyze_report(session, job_id: str, report_id: str, text: str, fund_type: str) -> None:
    analyzer = get_analyzer(fund_type)
    algorithm_version = analyzer.get_version()

    from sqlalchemy import and_, select
    stmt = select(ReportAnalysisModel).where(
        and_(
            ReportAnalysisModel.report_id == report_id,
            ReportAnalysisModel.algorithm_version == algorithm_version,
        )
    )
    existing = session.execute(stmt).scalar_one_or_none()
    if existing:
        _log_stage(session, job_id, "analyze", "skipped")
        return

    analyze_start = time.monotonic()
    _log_stage(session, job_id, "analyze", "started")

    report = session.get(ReportModel, report_id)
    if report:
        report.status = "analyzing"
        session.commit()

    result = analyzer.analyze(text)

    analysis = ReportAnalysisModel(
        report_id=report_id,
        algorithm_version=algorithm_version,
        detected_metrics=result.detected_metrics,
        weights=result.weights,
        quality_score=result.quality_score,
    )
    session.add(analysis)
    session.commit()

    analyze_ms = int((time.monotonic() - analyze_start) * 1000)
    _log_stage(session, job_id, "analyze", "completed", duration_ms=analyze_ms)

    _publish(events.REPORT_ANALYZED, {
        "report_id": report_id,
        "fund_type": fund_type,
        "quality_score": result.quality_score,
    })


def _score_report(session, job_id: str, report_id: str) -> None:
    from sqlalchemy import select
    from src.shared.infra.persistence.models import TransparencyScoreModel

    score_start = time.monotonic()
    _log_stage(session, job_id, "score", "started")

    try:
        report = session.get(ReportModel, report_id)
        if not report:
            return

        fund = session.get(FundModel, report.fund_id)
        if not fund:
            return

        rolling_window = env_service.analysis_rolling_window_months
        period_end = datetime.now()
        year_offset = rolling_window // 12
        month_offset = rolling_window % 12
        new_month = period_end.month - month_offset
        new_year = period_end.year - year_offset
        if new_month <= 0:
            new_month += 12
            new_year -= 1
        period_start = datetime(new_year, new_month, min(period_end.day, 28))

        # Check existing score
        stmt = select(TransparencyScoreModel).where(
            TransparencyScoreModel.fund_id == fund.id,
            TransparencyScoreModel.period_start == period_start,
            TransparencyScoreModel.period_end == period_end,
        )
        existing = session.execute(stmt).scalar_one_or_none()
        if existing:
            _log_stage(session, job_id, "score", "completed", duration_ms=int((time.monotonic() - score_start) * 1000))
            return

        # Get reports in period
        stmt = select(ReportModel).where(
            ReportModel.fund_id == fund.id,
            ReportModel.reference_month >= period_start,
            ReportModel.reference_month <= period_end,
        )
        reports_in_period = session.execute(stmt).scalars().all()

        report_ids = [r.id for r in reports_in_period]
        analyses = []
        if report_ids:
            stmt = select(ReportAnalysisModel).where(ReportAnalysisModel.report_id.in_(report_ids))
            analyses = session.execute(stmt).scalars().all()

        from src.shared.infra.adapters.scoring.implementations.weighted_transparency_score_calculator import (
            WeightedTransparencyScoreCalculator,
        )
        from src.shared.infra.adapters.scoring.ports.transparency_score_calculator import TransparencyScoreInput
        from src.shared.infra.persistence.mappers.sqlalchemy_mappers import ReportAnalysisMapper, ReportMapper

        domain_reports = [ReportMapper.to_domain(r) for r in reports_in_period]
        domain_analyses = [ReportAnalysisMapper.to_domain(a) for a in analyses]

        calculator = WeightedTransparencyScoreCalculator(env_service)
        result = calculator.calculate(
            TransparencyScoreInput(
                reports=domain_reports,
                analyses=domain_analyses,
                period_start=period_start,
                period_end=period_end,
            )
        )

        score_model = TransparencyScoreModel(
            fund_id=fund.id,
            period_start=period_start,
            period_end=period_end,
            regularity=result.regularity,
            timeliness=result.timeliness,
            quality=result.quality,
            final_score=result.final_score,
            classification=result.classification,
            algorithm_version=env_service.analysis_algorithm_version,
            metadata_={
                "reportCount": result.metadata.report_count,
                "expectedReports": result.metadata.expected_reports,
                "avgDelayDays": result.metadata.avg_delay_days,
                "avgQualityScore": result.metadata.avg_quality_score,
            },
        )
        session.add(score_model)
        session.commit()

        score_ms = int((time.monotonic() - score_start) * 1000)
        _log_stage(session, job_id, "score", "completed", duration_ms=score_ms)

        _publish(events.SCORE_CALCULATED, {
            "fund_id": fund.id,
            "final_score": result.final_score,
        })

    except Exception as e:
        score_ms = int((time.monotonic() - score_start) * 1000)
        _log_stage(session, job_id, "score", "failed", duration_ms=score_ms, metadata={"error": str(e)})
        logger.warning("Scoring failed for report %s: %s", report_id, str(e))


def _log_stage(
    session,
    processing_job_id: str,
    stage: str,
    status: str,
    duration_ms: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    log = ProcessingLogModel(
        processing_job_id=processing_job_id,
        stage=stage,
        status=status,
        duration_ms=duration_ms,
        metadata_=metadata,
    )
    session.add(log)
    session.commit()
