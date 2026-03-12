"""E2E tests for API key authentication."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_missing_api_key_returns_401(client: AsyncClient):
    response = await client.get("/equity/funds/test11/transparency")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing API key"


@pytest.mark.asyncio
async def test_invalid_api_key_returns_401(client: AsyncClient):
    response = await client.get(
        "/equity/funds/test11/transparency",
        headers={"x-api-key": "wrong-key"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid API key"


@pytest.mark.asyncio
async def test_valid_api_key_passes_auth(client: AsyncClient, auth_headers: dict):
    # Should get past auth (404 because fund doesn't exist, not 401)
    response = await client.get(
        "/equity/funds/nonexistent11/transparency",
        headers=auth_headers,
    )
    assert response.status_code == 404
