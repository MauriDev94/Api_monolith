from __future__ import annotations

import asyncio

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from loguru import logger
from starlette.types import Message, Receive, Scope, Send

from app.core.middleware.origin_check import OriginCheckMiddleware

ALLOWED_ORIGIN = "https://app.example.test"
EVIL_ORIGIN = "https://evil.example"
UNSAFE_METHODS = ["POST", "PUT", "PATCH", "DELETE"]


def _build_client(allowed_origins: list[str] | None = None) -> TestClient:
    """Tiny app: one handler for every method so we can tell whether routing was reached."""
    app = FastAPI()
    app.add_middleware(
        OriginCheckMiddleware,
        allowed_origins=[ALLOWED_ORIGIN] if allowed_origins is None else allowed_origins,
    )

    @app.api_route("/probe", methods=["GET", "HEAD", "POST", "PUT", "PATCH", "DELETE"])
    def probe() -> dict[str, str]:
        return {"reached": "handler"}

    return TestClient(app, raise_server_exceptions=False)


@pytest.mark.parametrize("method", UNSAFE_METHODS)
def test_unsafe_request_is_allowed_when_origin_is_configured(method: str) -> None:
    """An Origin that exactly matches the allowlist reaches the handler."""
    response = _build_client().request(method, "/probe", headers={"Origin": ALLOWED_ORIGIN})

    assert response.status_code == 200
    assert response.json() == {"reached": "handler"}


@pytest.mark.parametrize("method", UNSAFE_METHODS)
def test_unsafe_request_is_rejected_when_origin_is_not_configured(method: str) -> None:
    """A foreign Origin gets the standard 403 envelope and never reaches the handler."""
    response = _build_client().request(method, "/probe", headers={"Origin": EVIL_ORIGIN})

    assert response.status_code == 403
    assert response.json() == {"message": "Forbidden: origin not allowed"}
    assert "set-cookie" not in response.headers


def test_request_is_rejected_when_origin_is_null() -> None:
    """`Origin: null` (sandboxed iframes, some redirects) is never trusted."""
    response = _build_client().post("/probe", headers={"Origin": "null"})

    assert response.status_code == 403


def test_request_is_rejected_when_origin_only_matches_by_prefix() -> None:
    """Matching is exact: a look-alike host must not pass."""
    response = _build_client().post("/probe", headers={"Origin": f"{ALLOWED_ORIGIN}.evil.example"})

    assert response.status_code == 403


def test_request_is_allowed_when_no_origin_and_no_fetch_metadata() -> None:
    """Non-browser clients (curl, mobile, tests) send neither header and keep working."""
    response = _build_client().post("/probe")

    assert response.status_code == 200


def test_request_is_rejected_when_sec_fetch_site_is_cross_site_without_origin() -> None:
    """A browser that omitted Origin but sent Fetch Metadata is treated as hostile."""
    response = _build_client().post("/probe", headers={"Sec-Fetch-Site": "cross-site"})

    assert response.status_code == 403


def test_request_is_rejected_when_any_sec_fetch_header_is_present_without_origin() -> None:
    """Rule 3 covers every `Sec-Fetch-*` header, not only Sec-Fetch-Site."""
    response = _build_client().post("/probe", headers={"Sec-Fetch-Mode": "navigate"})

    assert response.status_code == 403


def test_request_is_allowed_when_sec_fetch_site_is_same_origin_with_unlisted_origin() -> None:
    """Same-origin requests (Vite proxy, Scalar docs) pass even if Origin is not configured."""
    response = _build_client().post(
        "/probe",
        headers={"Sec-Fetch-Site": "same-origin", "Origin": "http://localhost:5173"},
    )

    assert response.status_code == 200


def test_request_is_rejected_when_sec_fetch_site_is_same_site_with_evil_origin() -> None:
    """Only `same-origin` short-circuits; `same-site` still goes through the Origin check."""
    response = _build_client().post(
        "/probe", headers={"Sec-Fetch-Site": "same-site", "Origin": EVIL_ORIGIN}
    )

    assert response.status_code == 403


@pytest.mark.parametrize("method", ["GET", "HEAD"])
def test_safe_request_is_not_blocked_when_origin_is_foreign(method: str) -> None:
    """Safe methods are never inspected."""
    response = _build_client().request(
        method, "/probe", headers={"Origin": EVIL_ORIGIN, "Sec-Fetch-Site": "cross-site"}
    )

    assert response.status_code == 200


def test_options_preflight_is_not_blocked_when_origin_is_foreign() -> None:
    """OPTIONS passes untouched: the mini-app has no CORS, so routing answers 405 (not 403)."""
    response = _build_client().options(
        "/probe",
        headers={"Origin": EVIL_ORIGIN, "Access-Control-Request-Method": "POST"},
    )

    assert response.status_code == 405


def test_request_is_rejected_when_allowlist_is_empty_and_origin_is_present() -> None:
    """An empty allowlist trusts no browser origin."""
    response = _build_client(allowed_origins=[]).post("/probe", headers={"Origin": ALLOWED_ORIGIN})

    assert response.status_code == 403


def test_request_is_rejected_when_origin_has_trailing_slash() -> None:
    """Matching is exact: `https://app.example.test/` is not the configured origin."""
    response = _build_client().post("/probe", headers={"Origin": f"{ALLOWED_ORIGIN}/"})

    assert response.status_code == 403


def test_request_is_rejected_when_origin_differs_only_by_case() -> None:
    """Matching is case-sensitive: browsers send lowercase origins, so anything else is odd."""
    response = _build_client().post("/probe", headers={"Origin": ALLOWED_ORIGIN.upper()})

    assert response.status_code == 403


def test_request_is_rejected_when_sec_fetch_site_is_none_without_origin() -> None:
    """`Sec-Fetch-Site: none` (user-initiated navigation) with no Origin is still a browser."""
    response = _build_client().post("/probe", headers={"Sec-Fetch-Site": "none"})

    assert response.status_code == 403


def test_request_is_rejected_when_origin_header_is_duplicated() -> None:
    """Two Origin headers fail closed, even if both are allowed values."""
    response = _build_client().post(
        "/probe", headers=[("Origin", ALLOWED_ORIGIN), ("Origin", ALLOWED_ORIGIN)]
    )

    assert response.status_code == 403


def _run_asgi(method: str, headers: list[tuple[bytes, bytes]]) -> tuple[bool, int | None]:
    """Drive the middleware at ASGI level (lets us send values httpx would refuse)."""
    reached: list[bool] = []
    statuses: list[int] = []

    async def downstream(scope: Scope, receive: Receive, send: Send) -> None:
        reached.append(True)

    async def receive() -> Message:
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: Message) -> None:
        if message["type"] == "http.response.start":
            statuses.append(message["status"])

    scope: Scope = {
        "type": "http",
        "method": method,
        "path": "/probe",
        "query_string": b"",
        "headers": headers,
        "state": {},
    }
    middleware = OriginCheckMiddleware(downstream, allowed_origins=[ALLOWED_ORIGIN])
    asyncio.run(middleware(scope, receive, send))
    return bool(reached), statuses[0] if statuses else None


def test_request_is_rejected_when_method_is_lowercase_unsafe() -> None:
    """Fail closed: a non-canonical method is not in the safe allowlist, so it is checked."""
    reached, status = _run_asgi("post", [(b"origin", EVIL_ORIGIN.encode())])

    assert reached is False
    assert status == 403


def test_rejection_log_escapes_control_characters_and_truncates_origin() -> None:
    """Attacker-controlled Origin is logged via repr (no raw CRLF) and capped at 200 chars."""
    messages: list[str] = []
    sink_id = logger.add(lambda m: messages.append(m.record["message"]), level="WARNING")
    try:
        hostile = b"https://evil.example\r\nFAKE LOG LINE " + b"a" * 500
        reached, status = _run_asgi("POST", [(b"origin", hostile)])
    finally:
        logger.remove(sink_id)

    assert (reached, status) == (False, 403)
    assert len(messages) == 1
    assert "\r" not in messages[0]
    assert "\n" not in messages[0]
    assert "\\r\\n" in messages[0]
    assert "a" * 201 not in messages[0]
