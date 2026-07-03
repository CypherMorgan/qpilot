"""Health endpoint tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_returns_200(client: AsyncClient) -> None:
    """GET /api/v1/health returns 200 with healthy status."""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200

    body = response.json()
    assert body["data"]["status"] == "healthy"
    assert "app_name" in body["data"]
    assert "app_version" in body["data"]

    # Database check is present because test env uses SQLite
    db_check = body["data"]["checks"]["database"]
    assert db_check["status"] in ("healthy", "unhealthy")

    if db_check["status"] == "healthy":
        assert "latency_ms" in db_check

    assert "meta" in body
    assert "request_id" in body["meta"]


@pytest.mark.asyncio
async def test_health_includes_request_id(client: AsyncClient) -> None:
    """Health response includes an X-Request-ID header."""
    response = await client.get("/api/v1/health")
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) > 0


@pytest.mark.asyncio
async def test_health_response_meta_structure(client: AsyncClient) -> None:
    """Health response meta has the expected structure."""
    response = await client.get("/api/v1/health")
    body = response.json()

    meta = body["meta"]
    assert "request_id" in meta
    assert "timestamp" in meta
