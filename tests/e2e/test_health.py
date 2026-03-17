"""E2E tests for the health endpoint."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ("ok", "degraded")
    assert "timestamp" in data
    assert "db" in data


@pytest.mark.asyncio
async def test_health_db_is_up(client: AsyncClient):
    response = await client.get("/health")
    data = response.json()
    assert data["db"]["status"] == "up"
