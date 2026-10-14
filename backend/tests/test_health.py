"""Tests for health check endpoints."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test basic health check endpoint."""
    response = await client.get("/healthz")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "axiom-pilot-ryan-vo"
    assert data["version"] == "1.0.0"
    assert data["environment"] == "test"


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient):
    """Test readiness check with database."""
    response = await client.get("/healthz/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ready", "not_ready")
    assert data["database"] in ("connected", "disconnected")
    assert data["app"] == "axiom-pilot-ryan-vo"
    assert data["version"] == "1.0.0"