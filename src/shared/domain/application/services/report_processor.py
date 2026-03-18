import asyncio
import base64
import hashlib
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Any

import httpx

from src.shared.domain.application.repositories.report_analyses_repository import ReportAnalysesRepository
from src.shared.domain.application.repositories.report_contents_repository import ReportContentsRepository
from src.shared.domain.application.repositories.reports_repository import ReportsRepository
from src.shared.domain.enterprise.entities.report import Report
from src.shared.domain.enterprise.entities.report_analysis import ReportAnalysis
from src.shared.events.analyzer_registry import get_analyzer, get_content_validator

logger = logging.getLogger(__name__)

_executor = ThreadPoolExecutor(max_workers=2)


class PermanentFailure(Exception):
    """Errors that should not be retried (bad PDF, missing data)."""


@dataclass
class ProcessReportResult:
    report: Report
    analysis: ReportAnalysis
    cached: bool = False


class ReportProcessor:
    def __init__(
        self,
        reports_repository: ReportsRepository,
        report_contents_repository: ReportContentsRepository,
        report_analyses_repository: ReportAnalysesRepository,
    ) -> None:
        self._reports_repo = reports_repository
        self._contents_repo = report_contents_repository
        self._analyses_repo = report_analyses_repository

    async def process_report(
        self, report: Report, fund_type: str, force_redownload: bool = False,
    ) -> ProcessReportResult:
        existing_content = await self._contents_repo.find_by_report_id(report.id)

        if existing_content and not force_redownload:
            text = existing_content.raw_text
            page_count = existing_content.page_count
            logger.info("Using cached content for report %s", report.id)
        else:
            await self._reports_repo.update_status(report.id, "downloading")
            pdf_bytes = await self._download_pdf(report.pdf_url)
            pdf_hash = hashlib.sha256(pdf_bytes).hexdigest()
            await self._reports_repo.update_pdf_hash(report.id, pdf_hash)

            await self._reports_repo.update_status(report.id, "extracting")
            extracted = self._extract_pdf(pdf_bytes, fund_type)
            text = extracted["text"]
            page_count = extracted["page_count"]

            if not existing_content:
                await self._contents_repo.create(
                    report_id=report.id,
                    raw_text=text,
                    normalized_text=text.lower(),
                    page_count=page_count,
                    parser_version="1.0.0",
                )

        analyzer = get_analyzer(fund_type)
        algorithm_version = analyzer.get_version()

        existing_analysis = await self._analyses_repo.find_by_report_id_and_version(
            report.id, algorithm_version
        )
        if existing_analysis:
            await self._reports_repo.update_status(report.id, "completed")
            return ProcessReportResult(report=report, analysis=existing_analysis, cached=True)

        await self._reports_repo.update_status(report.id, "analyzing")
        loop = asyncio.get_running_loop()
        result = await loop.run_in_executor(_executor, analyzer.analyze, text)

        analysis = await self._analyses_repo.create(
            report_id=report.id,
            algorithm_version=algorithm_version,
            detected_metrics=result.detected_metrics,
            weights=result.weights,
            quality_score=result.quality_score,
        )

        await self._reports_repo.update_status(report.id, "completed")
        return ProcessReportResult(report=report, analysis=analysis)

    async def _download_pdf(self, url: str) -> bytes:
        transport = httpx.AsyncHTTPTransport(retries=3)
        async with httpx.AsyncClient(transport=transport, timeout=httpx.Timeout(60.0, connect=15.0)) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()

        raw = response.content
        text = response.text

        cleaned = text.strip().strip('"')
        if cleaned.startswith("JVBER"):
            return base64.b64decode(cleaned)

        if raw[:5] == b"%PDF-":
            return raw

        buf = text.encode("latin-1")
        if buf[:5] == b"%PDF-":
            return buf

        preview = text[:200] if len(text) > 200 else text
        raise PermanentFailure(f"Invalid PDF response (starts with: {preview[:80]})")

    def _extract_pdf(self, pdf_buffer: bytes, fund_type: str) -> dict[str, Any]:
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

        validator = get_content_validator(fund_type)
        validator.validate(text, page_count)

        return {"text": text, "page_count": page_count}
