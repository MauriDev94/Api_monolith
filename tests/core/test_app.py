import asyncio

import pytest
from fastapi.testclient import TestClient

from app import main as main_module
from app.main import app


# Tipo de test: Integration
def test_health_returns_503_when_db_is_down(monkeypatch: pytest.MonkeyPatch) -> None:
    """O3: /health responde 503 (readiness real) cuando la DB no responde."""

    def broken_session():
        raise RuntimeError("db down")
        yield  # pragma: no cover

    monkeypatch.setattr("app.core.providers.db.get_db_session", broken_session)
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json()["database"] == "unhealthy"


# Tipo de test: Integration
def test_lifespan_fails_fast_when_migration_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    """O2: si la migración de arranque falla, el lifespan re-lanza (no arranca con esquema roto)."""
    monkeypatch.setenv("APP_ENV", "production")

    def boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("migration boom")

    monkeypatch.setattr("alembic.command.upgrade", boom)

    async def run_lifespan() -> None:
        async with main_module.lifespan(app):
            pass

    with pytest.raises(RuntimeError, match="migration boom"):
        asyncio.run(run_lifespan())


# Tipo de test: Integration
def test_security_headers_present_on_api_responses() -> None:
    """S7: HSTS + CSP + nosniff presentes en respuestas de API."""
    client = TestClient(app, raise_server_exceptions=False)

    response = client.get("/")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert "max-age=" in response.headers["Strict-Transport-Security"]
    assert "default-src 'none'" in response.headers["Content-Security-Policy"]
    assert "X-XSS-Protection" not in response.headers
