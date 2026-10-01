import pytest
import sys
from pathlib import Path
from httpx import AsyncClient, ASGITransport

base_dir = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(base_dir / "backend"))

from app.main import app
from app.core.config import settings
from app.core.security import SESSION_COOKIE_NAME, CSRF_COOKIE_NAME


@pytest.mark.asyncio
async def test_health_ready_without_redis(monkeypatch):
    """Verify readiness check reports redis=False with an honest warning when REDIS_URL is empty."""
    monkeypatch.setattr(settings, "REDIS_URL", "")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000"
    ) as ac:
        res = await ac.get("/api/v1/health/ready")
        assert res.status_code == 200
        data = res.json()
        assert data["database"] is True
        assert data["redis"] is False
        assert "disabled/unset" in (data.get("redis_warning") or "")
        assert data["status"] == "ready"


@pytest.mark.asyncio
async def test_health_ready_unreachable_redis(monkeypatch):
    """Verify readiness check remains non-blocking (status 200) when Redis is unreachable."""
    monkeypatch.setattr(settings, "REDIS_URL", "redis://127.0.0.1:9999/0")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000"
    ) as ac:
        res = await ac.get("/api/v1/health/ready")
        assert res.status_code == 200
        data = res.json()
        assert data["database"] is True
        assert data["redis"] is False
        assert "unavailable" in (data.get("redis_warning") or "")


@pytest.mark.asyncio
async def test_cache_clear_without_redis(monkeypatch):
    """Verify cache clear returns cache_unavailable cleanly when REDIS_URL is empty."""
    monkeypatch.setattr(settings, "REDIS_URL", "")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000"
    ) as ac:
        res = await ac.post("/api/v1/cache/clear")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "cache_unavailable"


@pytest.mark.asyncio
async def test_cache_clear_unreachable_redis(monkeypatch):
    """Verify cache clear returns cache_unavailable cleanly when Redis is down."""
    monkeypatch.setattr(settings, "REDIS_URL", "redis://127.0.0.1:9999/0")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000"
    ) as ac:
        res = await ac.post("/api/v1/cache/clear")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "cache_unavailable"


@pytest.mark.asyncio
async def test_core_auth_flows_without_redis(monkeypatch):
    """Verify session creation, authentication, and /auth/me work completely without Redis."""
    monkeypatch.setattr(settings, "REDIS_URL", "")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac:
        login_res = await ac.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})
        assert login_res.status_code == 200
        assert SESSION_COOKIE_NAME in ac.cookies

        me_res = await ac.get("/api/v1/auth/me")
        assert me_res.status_code == 200
        assert me_res.json()["role"] == "MEDICAL_AFFAIRS"


@pytest.mark.asyncio
async def test_core_signals_and_overview_flows_without_redis(monkeypatch):
    """Verify signals retrieval and dashboard overview succeed with Redis disabled."""
    monkeypatch.setattr(settings, "REDIS_URL", "")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
        headers={"Origin": "http://localhost:3000"}
    ) as ac:
        # Sign in
        await ac.post("/api/v1/auth/demo-login", json={"role": "MEDICAL_AFFAIRS"})

        signals_res = await ac.get("/api/v1/signals?limit=5")
        assert signals_res.status_code == 200
        assert "signals" in signals_res.json()

        overview_res = await ac.get("/api/v1/overview")
        assert overview_res.status_code == 200
        assert "active_signals" in overview_res.json()
