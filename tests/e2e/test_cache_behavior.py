"""E2E tests specifically for Redis cache behavior across modules."""

import json

import pytest
import redis.asyncio as aioredis
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_cache_stores_valid_json(
    client: AsyncClient,
    auth_headers: dict,
    seed_fund_with_score: dict,
    redis_client: aioredis.Redis,
):
    """Verify cached values are valid JSON that matches the API response."""
    ticker = seed_fund_with_score["ticker"]

    response = await client.get(
        f"/equity/funds/{ticker}/transparency",
        headers=auth_headers,
    )

    cache_key = f"equity:transparency:{ticker.lower()}"
    raw = await redis_client.get(cache_key)
    cached_data = json.loads(raw)

    assert cached_data == response.json()


@pytest.mark.asyncio
async def test_cache_isolation_between_modules(
    client: AsyncClient,
    auth_headers: dict,
    seed_fund_with_score: dict,
    redis_client: aioredis.Redis,
):
    """Equity and mortgage caches use separate namespaces for the same ticker."""
    ticker = seed_fund_with_score["ticker"]

    # Hit equity endpoint
    await client.get(f"/equity/funds/{ticker}/transparency", headers=auth_headers)

    # Hit mortgage endpoint (returns data too since fund exists regardless of type)
    await client.get(f"/mortgage/funds/{ticker}/transparency", headers=auth_headers)

    equity_key = f"equity:transparency:{ticker.lower()}"
    mortgage_key = f"mortgage:transparency:{ticker.lower()}"

    # Both endpoints cache under their own namespace
    assert await redis_client.get(equity_key) is not None
    assert await redis_client.get(mortgage_key) is not None

    # Keys are different — invalidating one doesn't affect the other
    await redis_client.delete(equity_key)
    assert await redis_client.get(equity_key) is None
    assert await redis_client.get(mortgage_key) is not None


@pytest.mark.asyncio
async def test_cache_invalidation_on_discover(
    client: AsyncClient,
    auth_headers: dict,
    seed_fund_with_score: dict,
    redis_client: aioredis.Redis,
):
    """POST /discover invalidates transparency + history caches."""
    ticker = seed_fund_with_score["ticker"]

    # Populate caches
    await client.get(
        f"/equity/funds/{ticker}/transparency",
        headers=auth_headers,
    )
    await client.get(
        f"/equity/funds/{ticker}/transparency/history",
        headers=auth_headers,
    )

    transparency_key = f"equity:transparency:{ticker.lower()}"
    assert await redis_client.get(transparency_key) is not None

    # Discover — note: this will fail to actually discover because the ticker
    # is fake, but the cache invalidation happens before the collector runs
    await client.post(
        f"/equity/funds/{ticker}/discover",
        headers=auth_headers,
        json={},
    )

    # Transparency cache should be invalidated
    assert await redis_client.get(transparency_key) is None


@pytest.mark.asyncio
async def test_cache_not_set_for_404_responses(
    client: AsyncClient,
    auth_headers: dict,
    redis_client: aioredis.Redis,
):
    """404 responses should NOT be cached."""
    await client.get(
        "/equity/funds/nonexistent/transparency",
        headers=auth_headers,
    )

    key = "equity:transparency:nonexistent"
    assert await redis_client.get(key) is None


@pytest.mark.asyncio
async def test_history_different_params_different_cache_keys(
    client: AsyncClient,
    auth_headers: dict,
    seed_fund_with_score: dict,
    redis_client: aioredis.Redis,
):
    """Different pagination params produce separate cache entries."""
    ticker = seed_fund_with_score["ticker"]

    await client.get(
        f"/equity/funds/{ticker}/transparency/history",
        headers=auth_headers,
        params={"page": 1, "pageSize": 10, "order": "desc"},
    )
    await client.get(
        f"/equity/funds/{ticker}/transparency/history",
        headers=auth_headers,
        params={"page": 2, "pageSize": 10, "order": "desc"},
    )

    key1 = f"equity:transparency:history:{ticker.lower()}:p1:ps10:desc"
    key2 = f"equity:transparency:history:{ticker.lower()}:p2:ps10:desc"

    assert await redis_client.get(key1) is not None
    assert await redis_client.get(key2) is not None


@pytest.mark.asyncio
async def test_reprocess_invalidates_report_cache(
    client: AsyncClient,
    auth_headers: dict,
    seed_fund_with_report: dict,
    redis_client: aioredis.Redis,
):
    """POST /reprocess invalidates the cached report."""
    report_id = seed_fund_with_report["report_id"]

    # Populate report cache
    await client.get(
        f"/equity/reports/{report_id}",
        headers=auth_headers,
    )
    cache_key = f"equity:report:{report_id}"
    assert await redis_client.get(cache_key) is not None

    # Reprocess
    await client.post(
        "/equity/reports/reprocess",
        headers=auth_headers,
        json={"report_id": report_id},
    )

    # Cache should be invalidated
    assert await redis_client.get(cache_key) is None
