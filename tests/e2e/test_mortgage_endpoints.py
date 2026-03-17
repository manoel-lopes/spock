"""E2E tests for mortgage module endpoints."""

import uuid
from datetime import datetime

import pytest
from httpx import AsyncClient

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.shared.infra.env.env_service import env_service
from src.shared.infra.persistence.models import (
    ReportAnalysisModel,
    ReportContentModel,
    ReportModel,
    TransparencyScoreModel,
)

_test_engine = create_async_engine(env_service.database_url, poolclass=NullPool)
_test_session_factory = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
async def seed_mortgage_fund_with_score(seed_mortgage_fund: dict):
    """Mortgage fund with a transparency score."""
    score_id = str(uuid.uuid4())
    async with _test_session_factory() as session:
        score = TransparencyScoreModel(
            id=score_id,
            fund_id=seed_mortgage_fund["id"],
            period_start=datetime(2025, 1, 1),
            period_end=datetime(2026, 1, 1),
            regularity=0.6,
            timeliness=0.5,
            quality=0.7,
            final_score=0.6,
            classification="Moderada",
            algorithm_version="1.0.0-mortgage",
            metadata_={
                "reportCount": 7,
                "expectedReports": 12,
                "avgDelayDays": 10.0,
                "avgQualityScore": 0.7,
            },
        )
        session.add(score)
        await session.commit()

    yield {**seed_mortgage_fund, "score_id": score_id}


@pytest.fixture
async def seed_mortgage_fund_with_report(seed_mortgage_fund: dict):
    """Mortgage fund with a completed report."""
    report_id = str(uuid.uuid4())
    async with _test_session_factory() as session:
        report = ReportModel(
            id=report_id,
            fund_id=seed_mortgage_fund["id"],
            reference_month=datetime(2025, 6, 1),
            publication_date=datetime(2025, 7, 10),
            pdf_url="https://example.com/mortgage-test.pdf",
            pdf_hash="def456",
            status="completed",
        )
        session.add(report)
        await session.flush()

        content = ReportContentModel(
            report_id=report_id,
            raw_text="Relatório com rating de CRI e inadimplência controlada.",
            normalized_text="relatório com rating de cri e inadimplência controlada.",
            page_count=20,
            parser_version="1.0.0",
        )
        session.add(content)

        analysis = ReportAnalysisModel(
            report_id=report_id,
            algorithm_version="1.0.0-mortgage",
            detected_metrics={"cri_ratings": True, "nonperforming_comments": True, "subordination": False},
            weights={"cri_ratings": 1.0, "nonperforming_comments": 1.0, "subordination": 0.0},
            quality_score=0.133,
        )
        session.add(analysis)
        await session.commit()

    yield {**seed_mortgage_fund, "report_id": report_id}


# --- Transparency ---


@pytest.mark.asyncio
async def test_mortgage_get_transparency(
    client: AsyncClient,
    auth_headers: dict,
    seed_mortgage_fund_with_score: dict,
):
    ticker = seed_mortgage_fund_with_score["ticker"]
    response = await client.get(
        f"/mortgage/funds/{ticker}/transparency",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["score"]["final_score"] == 0.6
    assert data["score"]["classification"] == "Moderada"


@pytest.mark.asyncio
async def test_mortgage_get_transparency_history(
    client: AsyncClient,
    auth_headers: dict,
    seed_mortgage_fund_with_score: dict,
):
    ticker = seed_mortgage_fund_with_score["ticker"]
    response = await client.get(
        f"/mortgage/funds/{ticker}/transparency/history",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["totalItems"] == 1
    assert data["items"][0]["final_score"] == 0.6


# --- Reports ---


@pytest.mark.asyncio
async def test_mortgage_get_report(
    client: AsyncClient,
    auth_headers: dict,
    seed_mortgage_fund_with_report: dict,
):
    report_id = seed_mortgage_fund_with_report["report_id"]
    response = await client.get(
        f"/mortgage/reports/{report_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["report"]["status"] == "completed"
    assert data["analysis"]["algorithm_version"] == "1.0.0-mortgage"
    assert data["analysis"]["detected_metrics"]["cri_ratings"] is True


@pytest.mark.asyncio
async def test_mortgage_nonexistent_fund_returns_404(
    client: AsyncClient,
    auth_headers: dict,
):
    response = await client.get(
        "/mortgage/funds/zzzz9999/transparency",
        headers=auth_headers,
    )
    assert response.status_code == 404
