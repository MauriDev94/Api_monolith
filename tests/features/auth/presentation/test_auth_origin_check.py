# mypy: disable-error-code="attr-defined"
# Reason: same TestClient typing quirk as test_auth_api.py (per-file mypy mode only).

"""CSRF hardening: the real app must reject unsafe requests from untrusted origins.

These tests run against `app.main.app` (not a minimal app) so they pin the middleware
registration in `main.py`, not just the middleware class. The real use cases run on top
of `Mock(spec=<contract>)` ports, so "the use case did not run" is asserted on the ports.
"""

from __future__ import annotations

import secrets
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient
from httpx import Response

from app.features.auth.application.contracts.auth_datasource import AuthDatasource
from app.features.auth.application.contracts.password_manager import PasswordManager
from app.features.auth.application.contracts.token_manager import TokenManager
from app.features.auth.application.contracts.token_revocation_store import TokenRevocationStore
from app.features.auth.di.dependencies import (
    get_auth_repository,
    get_password_manager,
    get_token_manager,
    get_token_revocation_store,
)
from app.features.users.domain.entities.user import User
from app.features.users.domain.value_objects.email import Email
from app.main import app, settings

ALLOWED_ORIGIN = settings.cors_allowed_origins[0]
EVIL_ORIGIN = "https://evil.example"
VITE_ORIGIN = "http://localhost:5173"
COOKIE_KEY = "refresh_token"
FAR_FUTURE_EXP = 4_102_444_800  # 2100-01-01


@dataclass
class Ports:
    auth_datasource: Mock
    password_manager: Mock
    token_manager: Mock
    token_revocation_store: Mock


@pytest.fixture
def ports() -> Iterator[Ports]:
    """Override the auth ports with contract-spec'd mocks; real use cases run on top."""
    user = User(
        id="user-1",
        name="Test",
        lastname="User",
        email=Email("user@example.test"),
        password_hash=secrets.token_urlsafe(16),
        birthdate=date(2000, 1, 1),
    )
    auth_datasource = Mock(spec=AuthDatasource)
    auth_datasource.get_user_by_email.return_value = user
    password_manager = Mock(spec=PasswordManager)
    password_manager.verify_password.return_value = True
    token_manager = Mock(spec=TokenManager)
    token_manager.create_access_token.side_effect = lambda **_: secrets.token_urlsafe(16)
    token_manager.create_refresh_token.side_effect = lambda **_: secrets.token_urlsafe(16)
    token_manager.decode_refresh_token.return_value = {
        "sub": "user-1",
        "jti": secrets.token_urlsafe(8),
        "exp": FAR_FUTURE_EXP,
    }
    token_revocation_store = Mock(spec=TokenRevocationStore)
    token_revocation_store.is_revoked.return_value = False

    app.dependency_overrides[get_auth_repository] = lambda: auth_datasource
    app.dependency_overrides[get_password_manager] = lambda: password_manager
    app.dependency_overrides[get_token_manager] = lambda: token_manager
    app.dependency_overrides[get_token_revocation_store] = lambda: token_revocation_store
    try:
        yield Ports(auth_datasource, password_manager, token_manager, token_revocation_store)
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def client(ports: Ports) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def _login_form() -> dict[str, str]:
    return {"username": "user@example.test", "password": secrets.token_urlsafe(12)}


def _assert_standard_forbidden(response: Response) -> None:
    assert response.status_code == 403
    assert set(response.json()) == {"message"}
    assert "set-cookie" not in response.headers
    # Registered inside the security-headers and request-id middlewares.
    assert response.headers.get("x-request-id")
    assert response.headers.get("x-content-type-options")


def test_login_succeeds_and_sets_cookie_when_origin_is_allowed(
    client: TestClient, ports: Ports
) -> None:
    """Allowed Origin keeps today's behavior: 200 + refresh cookie."""
    response = client.post("/auth/v1/login", data=_login_form(), headers={"Origin": ALLOWED_ORIGIN})

    assert response.status_code == 200
    assert f"{COOKIE_KEY}=" in response.headers["set-cookie"]
    ports.token_revocation_store.store_active.assert_called_once()


def test_login_is_rejected_without_cookie_when_origin_is_evil(
    client: TestClient, ports: Ports
) -> None:
    """Login CSRF: a foreign form POST never reaches the use case nor overwrites the cookie."""
    response = client.post("/auth/v1/login", data=_login_form(), headers={"Origin": EVIL_ORIGIN})

    _assert_standard_forbidden(response)
    ports.auth_datasource.get_user_by_email.assert_not_called()
    ports.token_revocation_store.store_active.assert_not_called()


def test_login_is_rejected_when_origin_is_null(client: TestClient, ports: Ports) -> None:
    """`Origin: null` is rejected on login."""
    response = client.post("/auth/v1/login", data=_login_form(), headers={"Origin": "null"})

    _assert_standard_forbidden(response)
    ports.auth_datasource.get_user_by_email.assert_not_called()


def test_login_succeeds_when_request_has_no_origin_and_no_fetch_metadata(
    client: TestClient,
) -> None:
    """Non-browser clients (no Origin, no Sec-Fetch-*) are unaffected."""
    response = client.post("/auth/v1/login", data=_login_form())

    assert response.status_code == 200


def test_login_is_rejected_when_sec_fetch_site_is_cross_site_without_origin(
    client: TestClient, ports: Ports
) -> None:
    """A browser request flagged cross-site with no Origin is rejected."""
    response = client.post(
        "/auth/v1/login", data=_login_form(), headers={"Sec-Fetch-Site": "cross-site"}
    )

    _assert_standard_forbidden(response)
    ports.auth_datasource.get_user_by_email.assert_not_called()


def test_login_succeeds_when_sec_fetch_site_is_same_origin_with_unlisted_origin(
    client: TestClient,
) -> None:
    """Dev via the Vite proxy: same-origin wins even though localhost:5173 is not listed."""
    assert VITE_ORIGIN not in settings.cors_allowed_origins

    response = client.post(
        "/auth/v1/login",
        data=_login_form(),
        headers={"Sec-Fetch-Site": "same-origin", "Origin": VITE_ORIGIN},
    )

    assert response.status_code == 200


def test_refresh_keeps_session_alive_when_evil_request_is_blocked_first(
    client: TestClient, ports: Ports
) -> None:
    """Forced reuse-detection logout: the evil refresh is blocked, the real one still works."""
    client.cookies.set(COOKIE_KEY, secrets.token_urlsafe(16))

    evil = client.post("/auth/v1/refresh", headers={"Origin": EVIL_ORIGIN})

    _assert_standard_forbidden(evil)
    ports.token_manager.decode_refresh_token.assert_not_called()
    ports.token_revocation_store.revoke.assert_not_called()
    ports.token_revocation_store.revoke_all_for_user.assert_not_called()

    legit = client.post("/auth/v1/refresh", headers={"Origin": ALLOWED_ORIGIN})

    assert legit.status_code == 200
    ports.token_revocation_store.revoke.assert_called_once()
    ports.token_revocation_store.revoke_all_for_user.assert_not_called()


def test_logout_does_not_revoke_session_when_origin_is_evil(
    client: TestClient, ports: Ports
) -> None:
    """Forced global logout: the evil logout never runs, so the session survives."""
    client.cookies.set(COOKIE_KEY, secrets.token_urlsafe(16))

    evil = client.post("/auth/v1/logout", headers={"Origin": EVIL_ORIGIN})

    _assert_standard_forbidden(evil)
    ports.token_manager.decode_refresh_token.assert_not_called()
    ports.token_revocation_store.revoke_all_for_user.assert_not_called()

    follow_up = client.post("/auth/v1/refresh", headers={"Origin": ALLOWED_ORIGIN})

    assert follow_up.status_code == 200


def test_logout_revokes_session_when_origin_is_allowed(client: TestClient, ports: Ports) -> None:
    """Allowed Origin keeps today's behavior on logout: 204 and the session is revoked."""
    client.cookies.set(COOKIE_KEY, secrets.token_urlsafe(16))

    response = client.post("/auth/v1/logout", headers={"Origin": ALLOWED_ORIGIN})

    assert response.status_code == 204
    ports.token_revocation_store.revoke_all_for_user.assert_called_once_with("user-1")


def test_get_request_is_not_blocked_when_origin_is_evil(client: TestClient) -> None:
    """Safe methods are untouched by the origin check."""
    response = client.get("/", headers={"Origin": EVIL_ORIGIN})

    assert response.status_code == 200


def test_options_preflight_is_not_blocked_by_origin_check_when_origin_is_evil(
    client: TestClient,
) -> None:
    """CORS preflight is answered by the CORS middleware, never 403'd by the origin check."""
    response = client.options(
        "/auth/v1/login",
        headers={"Origin": EVIL_ORIGIN, "Access-Control-Request-Method": "POST"},
    )

    assert response.status_code != 403
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("PUT", "/v1/todos/some-todo-id"),
        ("DELETE", "/v1/todos/some-todo-id"),
    ],
)
def test_non_auth_unsafe_endpoint_is_rejected_when_origin_is_evil(
    client: TestClient, method: str, path: str
) -> None:
    """The check is app-wide: todos endpoints are protected without opting in."""
    response = client.request(method, path, headers={"Origin": EVIL_ORIGIN})

    _assert_standard_forbidden(response)
