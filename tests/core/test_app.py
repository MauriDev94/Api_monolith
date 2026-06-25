import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import main as main_module
from app.core.middleware.body_size_limit import BodySizeLimitMiddleware
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


# Tipo de test: Integration
def test_body_size_limit_rejects_oversized_request() -> None:
    """Un body que excede el límite se rechaza con 413 antes de llegar al endpoint."""
    mini_app = FastAPI()
    mini_app.add_middleware(BodySizeLimitMiddleware, max_body_bytes=10)

    @mini_app.post("/echo")
    def echo() -> dict[str, bool]:
        return {"ok": True}

    client = TestClient(mini_app, raise_server_exceptions=False)

    response = client.post("/echo", content=b"x" * 100)

    assert response.status_code == 413
    assert response.json()["message"] == "Request body too large"
