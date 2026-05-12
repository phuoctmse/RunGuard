from unittest.mock import AsyncMock

import httpx
import pytest

from reasoner.main import app


@pytest.fixture
async def client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(
        transport=transport, base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_healthz(client):
    resp = await client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_readyz(client):
    resp = await client.get("/readyz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}


@pytest.mark.asyncio
async def test_analyze_returns_result(client):
    mock_result = {
        "root_cause": "OOMKill",
        "confidence": 0.92,
        "actions": ["increase_memory_limit"],
    }

    mock_llm = AsyncMock()
    mock_llm.analyze_incident.return_value = mock_result
    app.state.llm = mock_llm

    resp = await client.post(
        "/analyze",
        params={
            "alert_name": "PodCrashLooping",
            "namespace": "production",
        },
        json={"logs": "OOMKilled"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["root_cause"] == "OOMKill"
    assert data["confidence"] == 0.92
