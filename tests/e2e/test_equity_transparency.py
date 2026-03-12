"""E2E tests for equity transparency endpoints with Redis caching."""

import pytest
import redis.asyncio as aioredis
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_transparency_returns_score(
    client: AsyncClient,
    auth_headers: dict,
    seed_fund_with_score: dict,
):
    ticker = seed_fund_with_score["ticker"]
    response = await client.get(
        f"/equity/funds/{ticker}/transparency",
        headers=auth_headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert "score" in data
    assert data["score"]["regularity"] == 0.8
    assert data["score"]["timeliness"] == 0.7
    assert data["score"]["quality"] == 0.9
    assert data["score"]["final_score"] == 0.81
    assert data["score"]["classification"] == "Alta"


@pytest.mark.asyncio
async def test_get_transparency_caches_response(
    client: AsyncClient,
    auth_headers: dict,
    seed_fund_with_score: dict,
    redis_client: aioredis.Redis,
):
    ticker = seed_fund_with_score["ticker"]
    cache_key = f"equity:transparency:{ticker.lower()}"

    # Verify cache is empty
    cached = await redis_client.get(cache_key)
    assert cached is None

    # First request — cache miss, hits DB
    response1 = await client.get(
        f"/equity/funds/{ticker}/transparency",
        headers=auth_headers,
    )
    assert response1.status_code == 200

    # Verify cache is populated
    cached = await redis_client.get(cache_key)
    assert cached is not None

    # Second request — should return cached data
    response2 = await client.get(
        f"/equity/funds/{ticker}/transparency",
        headers=auth_headers,
    )
    assert response2.status_code == 200
    assert response1.json() == response2.json()


@pytest.mark.asyncio
async def test_get_transparency_cache_has_ttl(
    client: AsyncClient,
    auth_headers: dict,
    seed_fund_with_score: dict,
    redis_client: aioredis.Redis,
):
    ticker = seed_fund_with_score["ticker"]
    cache_key = f"equity:transparency:{ticker.lower()}"

    await client.get(f"/equity/funds/{ticker}/transparency", headers=auth_headers)

    ttl = await redis_client.ttl(cache_key)
    assert 0 < ttl <= 600  # 10 min TTL


@pytest.mark.asyncio
async def test_get_transparency_nonexistent_fund_returns_404(
    client: AsyncClient,
    auth_headers: dict,
):
    response = await client.get(
        "/equity/funds/zzzz9999/transparency",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_transparency_fund_without_score_returns_404(
    client: AsyncClient,
    auth_headers: dict,
    seed_fund: dict,
):
    ticker = seed_fund["ticker"]
    response = await client.get(
        f"/equity/funds/{ticker}/transparency",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_transparency_history_returns_paginated(
    client: AsyncClient,
    auth_headers: dict,
    seed_fund_with_score: dict,
):
    ticker = seed_fund_with_score["ticker"]
    response = await client.get(
        f"/equity/funds/{ticker}/transparency/history",
        headers=auth_headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert data["page"] == 1
    assert data["pageSize"] == 20
    assert data["totalItems"] == 1
    assert data["totalPages"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["final_score"] == 0.81


@pytest.mark.asyncio
async def test_get_transparency_history_caches_response(
    client: AsyncClient,
    auth_headers: dict,
    seed_fund_with_score: dict,
    redis_client: aioredis.Redis,
):
    ticker = seed_fund_with_score["ticker"]
    cache_key = f"equity:transparency:history:{ticker.lower()}:p1:ps20:desc"

    # Cache miss
    assert await redis_client.get(cache_key) is None

    response1 = await client.get(
        f"/equity/funds/{ticker}/transparency/history",
        headers=auth_headers,
    )
    assert response1.status_code == 200

    # Cache hit
    assert await redis_client.get(cache_key) is not None

    response2 = await client.get(
        f"/equity/funds/{ticker}/transparency/history",
        headers=auth_headers,
    )
    assert response1.json() == response2.json()


@pytest.mark.asyncio
async def test_get_transparency_history_pagination_params(
    client: AsyncClient,
    auth_headers: dict,
    seed_fund_with_score: dict,
    redis_client: aioredis.Redis,
):
    ticker = seed_fund_with_score["ticker"]

    response = await client.get(
        f"/equity/funds/{ticker}/transparency/history",
        headers=auth_headers,
        params={"page": 1, "pageSize": 5, "order": "asc"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["pageSize"] == 5
    assert data["order"] == "asc"

    # Verify different pagination params produce different cache keys
    cache_key_asc = f"equity:transparency:history:{ticker.lower()}:p1:ps5:asc"
    assert await redis_client.get(cache_key_asc) is not None
