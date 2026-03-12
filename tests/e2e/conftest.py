"""
E2E test fixtures.

Uses the real FastAPI app with:
- Real production Redis (Upstash) for cache testing
- NullPool engine to avoid asyncpg connection conflicts in same event loop
- Dedicated SQLAlchemy session for test data setup/teardown
- Real API key auth
"""

import uuid
from collections.abc import AsyncGenerator

import pytest
import redis.asyncio as aioredis
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from src.shared.infra.env.env_service import env_service

# All tests share a session-scoped event loop (via pyproject.toml config),
# so a small connection pool is safe and avoids Neon cold-start timeouts.
_ENGINE_KWARGS = dict(
    pool_size=3,
    max_overflow=2,
    pool_pre_ping=True,
    pool_recycle=120,
    connect_args={"timeout": 60},
)

# Replace app's engine BEFORE importing the app.
import src.shared.infra.persistence.session as _session_mod

_test_app_engine = create_async_engine(env_service.database_url, **_ENGINE_KWARGS)
_test_app_session_factory = async_sessionmaker(
    _test_app_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

_session_mod.engine = _test_app_engine
_session_mod.async_session_factory = _test_app_session_factory


async def _patched_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with _test_app_session_factory() as session:
        yield session


_session_mod.get_session = _patched_get_session

# Now import the app (which uses the patched session module)
from src.main import app  # noqa: E402
from src.shared.infra.cache import redis_cache  # noqa: E402

API_KEY = env_service.api_key_list[0] if env_service.api_key_list else "test-key"

# Dedicated engine for test fixtures — separate pool from app
_test_engine = create_async_engine(env_service.database_url, **_ENGINE_KWARGS)
_test_session_factory = async_sessionmaker(
    _test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    return {"x-api-key": API_KEY}


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


@pytest.fixture
async def redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    r = aioredis.from_url(env_service.redis_url, decode_responses=True)
    yield r
    await r.aclose()


@pytest.fixture(autouse=True)
async def flush_cache_before_test(redis_client: aioredis.Redis):
    """Flush all cache keys before each test to ensure isolation."""
    await redis_client.flushdb()
    redis_cache._pool = None
    yield
    await redis_client.flushdb()


@pytest.fixture
async def seed_fund() -> AsyncGenerator[dict, None]:
    """Create a temporary equity fund directly in DB and clean up after test."""
    from src.shared.infra.persistence.models import FundModel

    ticker = f"test{uuid.uuid4().hex[:6]}11"
    fund_id = str(uuid.uuid4())

    async with _test_session_factory() as session:
        fund = FundModel(
            id=fund_id,
            ticker=ticker,
            name=f"Test Fund {ticker.upper()}",
            fund_type="equity",
            manager="Test Manager",
            category="tijolo",
            source="e2e-test",
            active=True,
        )
        session.add(fund)
        await session.commit()

    yield {"id": fund_id, "ticker": ticker}

    # Cleanup
    async with _test_session_factory() as session:
        from sqlalchemy import text
        await session.execute(text("DELETE FROM transparency_scores WHERE fund_id = :fid"), {"fid": fund_id})
        await session.execute(text("DELETE FROM report_analyses WHERE report_id IN (SELECT id FROM reports WHERE fund_id = :fid)"), {"fid": fund_id})
        await session.execute(text("DELETE FROM report_contents WHERE report_id IN (SELECT id FROM reports WHERE fund_id = :fid)"), {"fid": fund_id})
        await session.execute(text("DELETE FROM processing_logs WHERE processing_job_id IN (SELECT id FROM processing_jobs WHERE payload->>'fundId' = :fid)"), {"fid": fund_id})
        await session.execute(text("DELETE FROM processing_jobs WHERE payload->>'fundId' = :fid"), {"fid": fund_id})
        await session.execute(text("DELETE FROM reports WHERE fund_id = :fid"), {"fid": fund_id})
        await session.execute(text("DELETE FROM funds WHERE id = :fid"), {"fid": fund_id})
        await session.commit()


@pytest.fixture
async def seed_mortgage_fund() -> AsyncGenerator[dict, None]:
    """Create a temporary mortgage fund directly in DB and clean up after test."""
    from src.shared.infra.persistence.models import FundModel

    ticker = f"test{uuid.uuid4().hex[:6]}11"
    fund_id = str(uuid.uuid4())

    async with _test_session_factory() as session:
        fund = FundModel(
            id=fund_id,
            ticker=ticker,
            name=f"Test Mortgage Fund {ticker.upper()}",
            fund_type="mortgage",
            manager="Test Manager",
            category="papel",
            source="e2e-test",
            active=True,
        )
        session.add(fund)
        await session.commit()

    yield {"id": fund_id, "ticker": ticker}

    async with _test_session_factory() as session:
        from sqlalchemy import text
        await session.execute(text("DELETE FROM transparency_scores WHERE fund_id = :fid"), {"fid": fund_id})
        await session.execute(text("DELETE FROM report_analyses WHERE report_id IN (SELECT id FROM reports WHERE fund_id = :fid)"), {"fid": fund_id})
        await session.execute(text("DELETE FROM report_contents WHERE report_id IN (SELECT id FROM reports WHERE fund_id = :fid)"), {"fid": fund_id})
        await session.execute(text("DELETE FROM processing_logs WHERE processing_job_id IN (SELECT id FROM processing_jobs WHERE payload->>'fundId' = :fid)"), {"fid": fund_id})
        await session.execute(text("DELETE FROM processing_jobs WHERE payload->>'fundId' = :fid"), {"fid": fund_id})
        await session.execute(text("DELETE FROM reports WHERE fund_id = :fid"), {"fid": fund_id})
        await session.execute(text("DELETE FROM funds WHERE id = :fid"), {"fid": fund_id})
        await session.commit()


@pytest.fixture
async def seed_fund_with_score(seed_fund: dict) -> AsyncGenerator[dict, None]:
    """Create a fund with a transparency score for testing GET endpoints."""
    from datetime import datetime
    from src.shared.infra.persistence.models import TransparencyScoreModel

    score_id = str(uuid.uuid4())
    async with _test_session_factory() as session:
        score = TransparencyScoreModel(
            id=score_id,
            fund_id=seed_fund["id"],
            period_start=datetime(2025, 1, 1),
            period_end=datetime(2026, 1, 1),
            regularity=0.8,
            timeliness=0.7,
            quality=0.9,
            final_score=0.81,
            classification="Alta",
            algorithm_version="1.0.0",
            metadata_={
                "reportCount": 10,
                "expectedReports": 12,
                "avgDelayDays": 5.0,
                "avgQualityScore": 0.9,
            },
        )
        session.add(score)
        await session.commit()

    yield {**seed_fund, "score_id": score_id}


@pytest.fixture
async def seed_fund_with_report(seed_fund: dict) -> AsyncGenerator[dict, None]:
    """Create a fund with a completed report + analysis for testing."""
    from datetime import datetime
    from src.shared.infra.persistence.models import (
        ReportAnalysisModel,
        ReportContentModel,
        ReportModel,
    )

    report_id = str(uuid.uuid4())
    async with _test_session_factory() as session:
        report = ReportModel(
            id=report_id,
            fund_id=seed_fund["id"],
            reference_month=datetime(2025, 6, 1),
            publication_date=datetime(2025, 7, 10),
            pdf_url="https://example.com/test.pdf",
            pdf_hash="abc123",
            status="completed",
        )
        session.add(report)
        await session.flush()

        content = ReportContentModel(
            report_id=report_id,
            raw_text="Sample report text with vacância física and cap rate metrics.",
            normalized_text="sample report text with vacância física and cap rate metrics.",
            page_count=15,
            parser_version="1.0.0",
        )
        session.add(content)

        analysis = ReportAnalysisModel(
            report_id=report_id,
            algorithm_version="1.0.0",
            detected_metrics={"vacancia_fisica": True, "cap_rate": True, "walt": False},
            weights={"vacancia_fisica": 1.0, "cap_rate": 1.0, "walt": 0.0},
            quality_score=0.2,
        )
        session.add(analysis)
        await session.commit()

    yield {**seed_fund, "report_id": report_id}
