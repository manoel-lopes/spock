import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def new_uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class FundModel(Base):
    __tablename__ = "funds"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    ticker: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    fund_type: Mapped[str] = mapped_column(String, default="equity", server_default="equity", nullable=False)
    manager: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class ReportModel(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    fund_id: Mapped[str] = mapped_column(String, nullable=False)
    reference_month: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    publication_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    pdf_url: Mapped[str] = mapped_column(String, nullable=False)
    pdf_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class ReportContentModel(Base):
    __tablename__ = "report_contents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    report_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False)
    parser_version: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class ReportAnalysisModel(Base):
    __tablename__ = "report_analyses"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    report_id: Mapped[str] = mapped_column(String, nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String, nullable=False)
    detected_metrics: Mapped[dict] = mapped_column(JSONB, nullable=False)
    weights: Mapped[dict] = mapped_column(JSONB, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class TransparencyScoreModel(Base):
    __tablename__ = "transparency_scores"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    fund_id: Mapped[str] = mapped_column(String, nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    regularity: Mapped[float] = mapped_column(Float, nullable=False)
    timeliness: Mapped[float] = mapped_column(Float, nullable=False)
    quality: Mapped[float] = mapped_column(Float, nullable=False)
    final_score: Mapped[float] = mapped_column(Float, nullable=False)
    classification: Mapped[str] = mapped_column(String, nullable=False)
    algorithm_version: Mapped[str] = mapped_column(String, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class ProcessingJobModel(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    external_job_id: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending", nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class ProcessingLogModel(Base):
    __tablename__ = "processing_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    processing_job_id: Mapped[str] = mapped_column(String, nullable=False)
    stage: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class IncidentReportModel(Base):
    __tablename__ = "incident_reports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    fund_id: Mapped[str] = mapped_column(String, nullable=False)
    type: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)


class ReportSourceModel(Base):
    __tablename__ = "report_sources"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=new_uuid)
    report_id: Mapped[str] = mapped_column(String, nullable=False)
    source_type: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[str] = mapped_column(String, nullable=False)
    discovered_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    reliability: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    metadata_: Mapped[dict | None] = mapped_column("metadata", JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
