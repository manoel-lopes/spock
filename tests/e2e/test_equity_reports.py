"""E2E tests for equity report endpoints."""

import pytest
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
async def test_get_report_nonexistent_returns_404(
    client: AsyncClient,
    auth_headers: dict,
):
    response = await client.get(
        "/equity/reports/nonexistent-id",
        headers=auth_headers,
    )
    assert response.status_code == 404
