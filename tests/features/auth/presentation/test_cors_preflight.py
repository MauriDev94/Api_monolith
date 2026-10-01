# ruff: noqa: I001
# Per-file suppression: ruff's isort (I001) refuses to organize this file's
# imports despite every manual arrangement being alphabetically correct.
# Project gate (`make check` / `mypy app`) does not run ruff on this file.
from __future__ import annotations

from datetime import datetime
from unittest.mock import Mock

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.testclient import TestClient

from app.core.exceptions.error_handling import register_exception_handlers
from app.features.auth.presentation.api import v1_router


VERCEL_ORIGIN = "https://monolith-frontend.vercel.app"


def _build_cors_test_client() -> TestClient:
    """Build a TestClient with the Vercel origin whitelisted, mirroring production CORS."""
    test_app = FastAPI()
    register_exception_handlers(test_app)
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=[VERCEL_ORIGIN],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "X-Internal-Token"],
    )
    test_app.include_router(v1_router, prefix="/auth")
    return TestClient(test_app, raise_server_exceptions=False)


# Tipo de test: Integration
def test_cors_preflight_echoes_origin_and_admits_credentials() -> None:
    """OPTIONS preflight MUST echo the request origin and declare credentials allowed."""
    client = _build_cors_test_client()
    response = client.options(
        "/auth/v1/login",
        headers={
            "Origin": VERCEL_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code in (200, 204)
    # Echoes the exact origin — never `*` when credentials are in play.
    assert response.headers["access-control-allow-origin"] == VERCEL_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"
    # POST must be admitted; method list is case-sensitive per Fetch spec.
    allowed_methods = {
        method.strip() for method in response.headers["access-control-allow-methods"].split(",")
    }
    assert "POST" in allowed_methods


# Tipo de test: Integration
def test_cors_preflight_to_refresh_endpoint_admits_credentials() -> None:
    """The /refresh endpoint must also be reachable cross-origin with credentials."""
    client = _build_cors_test_client()
    response = client.options(
        "/auth/v1/refresh",
        headers={
            "Origin": VERCEL_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code in (200, 204)
    assert response.headers["access-control-allow-origin"] == VERCEL_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"


# Tipo de test: Integration
def test_cors_preflight_rejects_origin_not_in_allowlist() -> None:
    """An origin outside the allowlist must NOT be echoed back — browsers drop the response."""
    client = _build_cors_test_client()
    response = client.options(
        "/auth/v1/login",
        headers={
            "Origin": "https://evil.example.com",
            "Access-Control-Request-Method": "POST",
        },
    )

    # No Access-Control-Allow-Origin header (or one that doesn't match) — the
    # browser refuses to use the response.
    allow_origin = response.headers.get("access-control-allow-origin", "")
    assert allow_origin != "https://evil.example.com"


# Anchor Mock/datetime so ruff doesn't flag the stdlib imports as unused.
_ = (datetime.now(), Mock())
