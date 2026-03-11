from src.domain.enterprise.entities.fund import Fund
from src.domain.enterprise.entities.processing_job import ProcessingJob
from src.domain.enterprise.entities.processing_log import ProcessingLog
from src.domain.enterprise.entities.report import Report
from src.domain.enterprise.entities.report_analysis import ReportAnalysis
from src.domain.enterprise.entities.report_content import ReportContent
from src.domain.enterprise.entities.transparency_score import TransparencyScore
from src.infra.persistence.models import (
    FundModel,
    ProcessingJobModel,
    ProcessingLogModel,
    ReportAnalysisModel,
    ReportContentModel,
    ReportModel,
    TransparencyScoreModel,
)


class FundMapper:
    @staticmethod
    def to_domain(model: FundModel) -> Fund:
        return Fund(
            id=model.id,
            ticker=model.ticker,
            name=model.name,
            manager=model.manager,
            category=model.category,
            source=model.source,
            active=model.active,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class ReportMapper:
    @staticmethod
    def to_domain(model: ReportModel) -> Report:
        return Report(
            id=model.id,
            fund_id=model.fund_id,
            reference_month=model.reference_month,
            publication_date=model.publication_date,
            pdf_url=model.pdf_url,
            pdf_hash=model.pdf_hash,
            status=model.status,
            error_message=model.error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class ReportContentMapper:
    @staticmethod
    def to_domain(model: ReportContentModel) -> ReportContent:
        return ReportContent(
            id=model.id,
            report_id=model.report_id,
            raw_text=model.raw_text,
            normalized_text=model.normalized_text,
            page_count=model.page_count,
            parser_version=model.parser_version,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class ReportAnalysisMapper:
    @staticmethod
    def to_domain(model: ReportAnalysisModel) -> ReportAnalysis:
        return ReportAnalysis(
            id=model.id,
            report_id=model.report_id,
            algorithm_version=model.algorithm_version,
            detected_metrics=model.detected_metrics,
            weights=model.weights,
            quality_score=model.quality_score,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class TransparencyScoreMapper:
    @staticmethod
    def to_domain(model: TransparencyScoreModel) -> TransparencyScore:
        return TransparencyScore(
            id=model.id,
            fund_id=model.fund_id,
            period_start=model.period_start,
            period_end=model.period_end,
            regularity=model.regularity,
            timeliness=model.timeliness,
            quality=model.quality,
            final_score=model.final_score,
            classification=model.classification,
            algorithm_version=model.algorithm_version,
            metadata=model.metadata_,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class ProcessingJobMapper:
    @staticmethod
    def to_domain(model: ProcessingJobModel) -> ProcessingJob:
        return ProcessingJob(
            id=model.id,
            external_job_id=model.external_job_id,
            type=model.type,
            payload=model.payload,
            status=model.status,
            attempts=model.attempts,
            started_at=model.started_at,
            completed_at=model.completed_at,
            error_message=model.error_message,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


class ProcessingLogMapper:
    @staticmethod
    def to_domain(model: ProcessingLogModel) -> ProcessingLog:
        return ProcessingLog(
            id=model.id,
            processing_job_id=model.processing_job_id,
            stage=model.stage,
            status=model.status,
            duration_ms=model.duration_ms,
            metadata=model.metadata_,
            created_at=model.created_at,
        )
