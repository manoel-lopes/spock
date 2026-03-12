"""E2E tests for equity report endpoints with Redis caching."""

import pytest
import redis.asyncio as aioredis
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_report_returns_completed_analysis(
    client: AsyncClient,
    auth_headers: dict,
    seed_fund_with_report: dict,
):
    report_id = seed_fund_with_report["report_id"]
    response = await client.get(
        f"/equity/reports/{report_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert data["report"]["status"] == "completed"
    assert data["content"] is not None
    assert data["content"]["page_count"] == 15
    assert data["analysis"] is not None
    assert data["analysis"]["quality_score"] == 0.2
    assert data["analysis"]["detected_metrics"]["vacancia_fisica"] is True
    assert data["analysis"]["detected_metrics"]["cap_rate"] is True
    assert data["analysis"]["detected_metrics"]["walt"] is False


@pytest.mark.asyncio
async def test_get_report_caches_completed_report(
    client: AsyncClient,
    auth_headers: dict,
    seed_fund_with_report: dict,
    redis_client: aioredis.Redis,
):
    report_id = seed_fund_with_report["report_id"]
    cache_key = f"equity:report:{report_id}"

    # Cache miss
    assert await redis_client.get(cache_key) is None

    response1 = await client.get(
        f"/equity/reports/{report_id}",
        headers=auth_headers,
    )
    assert response1.status_code == 200

    # Cache hit — completed reports get cached with 1 hour TTL
    cached = await redis_client.get(cache_key)
    assert cached is not None

    ttl = await redis_client.ttl(cache_key)
    assert 0 < ttl <= 3600

    # Second request returns same data from cache
    response2 = await client.get(
        f"/equity/reports/{report_id}",
        headers=auth_headers,
    )
    assert response1.json() == response2.json()


@pytest.mark.asyncio
async def test_get_report_nonexistent_returns_404(
    client: AsyncClient,
    auth_headers: dict,
):
    response = await client.get(
        "/equity/reports/nonexistent-id",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_submit_analysis_nonexistent_fund_returns_404(
    client: AsyncClient,
    auth_headers: dict,
):
    response = await client.post(
        "/equity/reports/analyze",
        headers=auth_headers,
        json={
            "ticker": "zzzz9999",
            "pdf_url": "https://example.com/test.pdf",
            "reference_month": "2025-06-01T00:00:00",
        },
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_submit_analysis_creates_job(
    client: AsyncClient,
    auth_headers: dict,
    seed_fund: dict,
):
    ticker = seed_fund["ticker"]
    response = await client.post(
        "/equity/reports/analyze",
        headers=auth_headers,
        json={
            "ticker": ticker,
            "pdf_url": "https://example.com/test.pdf",
            "reference_month": "2025-06-01T00:00:00",
        },
    )
    assert response.status_code == 202

    data = response.json()
    assert "jobId" in data
    assert "reportId" in data


@pytest.mark.asyncio
async def test_submit_analysis_invalidates_transparency_cache(
    client: AsyncClient,
    auth_headers: dict,
    seed_fund_with_score: dict,
    redis_client: aioredis.Redis,
):
    ticker = seed_fund_with_score["ticker"]

    # Populate the transparency cache
    await client.get(
        f"/equity/funds/{ticker}/transparency",
        headers=auth_headers,
    )
    cache_key = f"equity:transparency:{ticker.lower()}"
    assert await redis_client.get(cache_key) is not None

    # Submit analysis — should invalidate the cache
    await client.post(
        "/equity/reports/analyze",
        headers=auth_headers,
        json={
            "ticker": ticker,
            "pdf_url": "https://example.com/new-report.pdf",
            "reference_month": "2025-07-01T00:00:00",
        },
    )

    # Cache should be invalidated
    assert await redis_client.get(cache_key) is None
